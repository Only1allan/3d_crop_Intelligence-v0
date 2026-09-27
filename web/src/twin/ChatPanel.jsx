import { useEffect, useMemo, useRef, useState } from 'react'
import { Send, Mic, MicOff, Volume2, VolumeX, Square, Sparkles, KeyRound, WifiOff, BookOpen } from 'lucide-react'
import { buildMessages } from '../lib/rag'
import { chat, hasKey, setKey, MODEL_LABEL } from '../lib/llm'
import { offlineAnswer } from '../lib/offline'

function chipsFor(zone) {
  if (!zone) return ['Which plot needs me most today?', 'Compare soil pH across the farm', 'Where is blight risk highest?', 'Is any of this live sensor data?']
  const n = zone.zoneId
  return [`How is ${n} doing?`, 'Should I irrigate this plot?', "What's the pH? Do I need lime?", 'Any blight risk?', 'When can I harvest?', 'What should I apply this week?']
}

// tiny formatter: **bold**, bullet lines, paragraphs
function Rich({ text }) {
  const lines = text.split('\n').filter((l, i, a) => l.trim() || (i && a[i - 1].trim()))
  return lines.map((l, i) => {
    const bullet = /^\s*[-*•]\s+/.test(l)
    const body = l.replace(/^\s*[-*•]\s+/, '').replace(/^#+\s*/, '')
    const parts = body.split(/(\*\*[^*]+\*\*)/g).map((p, j) => p.startsWith('**') ? <b key={j}>{p.slice(2, -2)}</b> : p)
    return bullet ? <div key={i} className="b-li">{parts}</div> : body.trim() ? <p key={i}>{parts}</p> : null
  })
}

const SR = typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition)

export default function ChatPanel({ zone }) {
  const ctxKey = zone?.zoneId || 'farm'
  const [threads, setThreads] = useState({})
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [speak, setSpeak] = useState(false)
  const [listening, setListening] = useState(false)
  const [keyOk, setKeyOk] = useState(hasKey())
  const [askKey, setAskKey] = useState(false)
  const abortRef = useRef(null)
  const scroller = useRef(null)
  const recRef = useRef(null)
  const msgs = threads[ctxKey] || []
  const chips = useMemo(() => chipsFor(zone), [zone])

  useEffect(() => { scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: 'smooth' }) }, [msgs])
  useEffect(() => () => { abortRef.current?.abort(); window.speechSynthesis?.cancel() }, [])

  const update = (key, fn) => setThreads((t) => ({ ...t, [key]: fn(t[key] || []) }))

  async function ask(q) {
    const question = q.trim()
    if (!question || busy) return
    setInput('')
    const key = ctxKey
    const history = msgs.filter((m) => !m.error).map((m) => ({ role: m.role, content: m.content }))
    const { msgs: payload, docs } = buildMessages(history, question, zone)
    const sources = docs.map((d) => d.title)
    update(key, (m) => [...m, { role: 'user', content: question }, { role: 'assistant', content: '', streaming: true, sources }])
    setBusy(true)
    const ctrl = new AbortController(); abortRef.current = ctrl
    const patch = (p) => update(key, (m) => { const c = [...m]; c[c.length - 1] = { ...c[c.length - 1], ...p }; return c })
    let final = ''
    try {
      const { text, model } = await chat(payload, (t) => patch({ content: t }), ctrl.signal)
      final = text
      patch({ content: text, streaming: false, model })
    } catch (e) {
      if (ctrl.signal.aborted) { patch({ streaming: false, content: '(stopped)' }); setBusy(false); return }
      final = offlineAnswer(question, zone)
      patch({ content: final, streaming: false, offline: true, reason: e.message === 'no-key' ? 'no API key' : 'AI service unreachable' })
    }
    setBusy(false)
    if (speak && final && window.speechSynthesis) {
      window.speechSynthesis.cancel()
      const u = new SpeechSynthesisUtterance(final.replace(/\*\*/g, '').replace(/^\s*[-*•]\s+/gm, ''))
      u.rate = 1.03; window.speechSynthesis.speak(u)
    }
  }

  function toggleMic() {
    if (!SR) return
    if (listening) { recRef.current?.stop(); return }
    const r = new SR(); recRef.current = r
    r.lang = 'en-US'; r.interimResults = true; r.continuous = false
    r.onresult = (e) => {
      const t = Array.from(e.results).map((x) => x[0].transcript).join('')
      setInput(t)
      if (e.results[e.results.length - 1].isFinal) { r.stop(); ask(t) }
    }
    r.onend = () => setListening(false)
    r.onerror = () => setListening(false)
    setListening(true); r.start()
  }

  const lastA = [...msgs].reverse().find((m) => m.role === 'assistant' && !m.streaming)
  const lastOffline = lastA?.offline
  const lastModel = lastA?.model

  return (
    <div className="chat">
      <div className="chat-head">
        <div className="chat-title">
          <Sparkles size={16} className="accent" />
          <span>Talking to <b>{zone ? `Plot ${zone.zoneId} · ${zone.displayName}` : 'the whole farm'}</b></span>
        </div>
        <div className="chat-tools">
          <button className={`icon-btn sm ${speak ? 'on' : ''}`} title={speak ? 'Voice replies on' : 'Read answers aloud'} onClick={() => { setSpeak((s) => !s); window.speechSynthesis?.cancel() }}>
            {speak ? <Volume2 size={15} /> : <VolumeX size={15} />}
          </button>
          <button className="icon-btn sm" title="OpenRouter key" onClick={() => setAskKey((s) => !s)}><KeyRound size={15} /></button>
        </div>
      </div>
      <div className="chat-badges">
        <span className="chip">{lastOffline ? <><WifiOff size={12} /> offline answers</> : <>LLM: {lastModel ? MODEL_LABEL(lastModel) : 'NVIDIA Nemotron'} · OpenRouter free tier</>}</span>
        <span className="chip gray"><BookOpen size={12} /> RAG over farm data</span>
      </div>
      {askKey && (
        <form className="keybox" onSubmit={(e) => { e.preventDefault(); const v = e.target.k.value; setKey(v); setKeyOk(hasKey()); setAskKey(false) }}>
          <input name="k" type="password" placeholder={keyOk ? 'Key set. Paste to replace' : 'Paste OpenRouter key (sk-or-...)'} autoComplete="off" />
          <button className="btn btn-primary btn-sm" type="submit">Save</button>
        </form>
      )}

      <div className="chat-log" ref={scroller} aria-live="polite">
        {msgs.length === 0 && (
          <div className="chat-empty">
            <p>{zone ? <>Ask <b>{zone.displayName}</b> anything. Answers come from this plot's numbers.</> : <>Ask about the whole farm, or click a plot to talk to it directly.</>}</p>
          </div>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>
            {m.role === 'assistant' ? (
              <>
                {m.content ? <Rich text={m.content} /> : <div className="typing"><i /><i /><i /></div>}
                {!m.streaming && m.content && (
                  <div className="b-meta">
                    {m.offline ? <span className="b-model off"><WifiOff size={11} /> offline advisor · {m.reason}</span>
                      : m.model && <span className="b-model"><Sparkles size={11} /> {MODEL_LABEL(m.model)}</span>}
                    {m.sources?.slice(0, 4).map((s) => <span key={s} className="b-src">{s}</span>)}
                  </div>
                )}
              </>
            ) : m.content}
          </div>
        ))}
      </div>

      <div className="chat-chips">
        {chips.map((c) => <button key={c} disabled={busy} onClick={() => ask(c)}>{c}</button>)}
      </div>
      <form className="chat-input" onSubmit={(e) => { e.preventDefault(); ask(input) }}>
        {SR && (
          <button type="button" className={`icon-btn ${listening ? 'rec' : ''}`} onClick={toggleMic} title="Speak your question" aria-label="Speak your question">
            {listening ? <MicOff size={18} /> : <Mic size={18} />}
          </button>
        )}
        <input value={input} onChange={(e) => setInput(e.target.value)} placeholder={listening ? 'Listening…' : zone ? `Ask ${zone.zoneId} anything…` : 'Ask your farm anything…'} aria-label="Question" />
        {busy ? (
          <button type="button" className="icon-btn send" onClick={() => abortRef.current?.abort()} aria-label="Stop"><Square size={16} /></button>
        ) : (
          <button type="submit" className="icon-btn send" disabled={!input.trim()} aria-label="Send"><Send size={17} /></button>
        )}
      </form>
    </div>
  )
}
