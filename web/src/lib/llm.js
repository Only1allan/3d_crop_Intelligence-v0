// OpenRouter client: streamed chat completions with a model fallback chain.
// The key ships to the browser (static demo). Put a spend cap on it.
const ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions'

export const MODELS = [
  import.meta.env.VITE_OPENROUTER_MODEL,
  'nvidia/nemotron-3-super-120b-a12b:free',
  'google/gemma-4-31b-it:free',
  'qwen/qwen3.8-27b:free',
  'nvidia/nemotron-3.5-lightning:free',
].filter((m, i, a) => m && a.indexOf(m) === i)

// Models that answered 400/404 (bad id) are skipped for the rest of the session.
const dead = new Set()

export const MODEL_LABEL = (id = '') => {
  if (id.includes('nemotron-3-super')) return 'NVIDIA Nemotron 3 Super'
  if (id.includes('nemotron')) return 'NVIDIA Nemotron'
  if (id.includes('gemma')) return 'Google Gemma 4'
  if (id.includes('qwen')) return 'Qwen 3.8'
  return id.split('/').pop()?.replace(':free', '') || 'LLM'
}

const LS_KEY = 'oci.openrouterKey'
export function getKey() {
  try { return localStorage.getItem(LS_KEY) || import.meta.env.VITE_OPENROUTER_API_KEY || '' } catch { return import.meta.env.VITE_OPENROUTER_API_KEY || '' }
}
export function setKey(k) { try { k ? localStorage.setItem(LS_KEY, k.trim()) : localStorage.removeItem(LS_KEY) } catch { /* private mode */ } }
export const hasKey = () => !!getKey()

const LEAK = /^\s*(<think>|here'?s a thinking process|thinking process|okay,? (so|let'?s|let me)|let me think|1\.\s*analy[sz]e)/i
const LEAK_PREFIX = /^\s*(<|h|t|o|l|1)/i

async function streamOnce(model, messages, onToken, signal) {
  const ctrl = new AbortController()
  const abort = () => ctrl.abort()
  signal?.addEventListener('abort', abort)
  const firstTokenTimer = setTimeout(abort, 30000)
  try {
    const res = await fetch(ENDPOINT, {
      method: 'POST',
      signal: ctrl.signal,
      headers: {
        Authorization: `Bearer ${getKey()}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': location.origin,
        'X-Title': 'Omniverse Crop Intelligence',
      },
      body: JSON.stringify({ model, messages, stream: true, temperature: 0.3, max_tokens: 700, reasoning: { enabled: false } }),
    })
    if (res.status === 400 || res.status === 404) dead.add(model)
    if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}: ${(await res.text().catch(() => '')).slice(0, 160)}`)
    const reader = res.body.getReader()
    const dec = new TextDecoder()
    let buf = '', text = ''
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      buf += dec.decode(value, { stream: true })
      const lines = buf.split('\n')
      buf = lines.pop()
      for (const line of lines) {
        const l = line.trim()
        if (!l.startsWith('data:')) continue
        const data = l.slice(5).trim()
        if (data === '[DONE]') continue
        try {
          const j = JSON.parse(data)
          if (j.error) throw new Error(j.error.message || 'stream error')
          const delta = j.choices?.[0]?.delta?.content
          if (delta) {
            if (!text) clearTimeout(firstTokenTimer)
            text += delta
            // Some free models leak chain-of-thought into content: reject and fall through.
            if (text.length < 120 && LEAK.test(text)) throw new Error('reasoning leak')
            if (text.length >= 24 || !LEAK_PREFIX.test(text)) onToken(text.replace(/^\s+/, ''))
          }
        } catch (e) { if (e instanceof SyntaxError) continue; throw e }
      }
    }
    if (!text.trim()) throw new Error('empty answer')
    onToken(text.trim())
    return text.trim()
  } finally {
    clearTimeout(firstTokenTimer)
    signal?.removeEventListener('abort', abort)
  }
}

// Tries each model in order. Throws only if every model fails (caller falls back offline).
export async function chat(messages, onToken, signal) {
  if (!hasKey()) throw new Error('no-key')
  let lastErr
  for (const model of MODELS) {
    if (dead.has(model)) continue
    for (let attempt = 0; attempt < 2; attempt++) {
      try {
        const text = await streamOnce(model, messages, onToken, signal)
        return { text, model }
      } catch (e) {
        if (signal?.aborted) throw e
        lastErr = e
        console.warn('[advisor] model failed:', model, e.message)
        const transient = /overload|429|rate|temporar|timeout|network|fetch/i.test(e.message)
        if (!transient || attempt) break
        await new Promise((r) => setTimeout(r, 1200))
      }
    }
  }
  throw lastErr || new Error('all models failed')
}
