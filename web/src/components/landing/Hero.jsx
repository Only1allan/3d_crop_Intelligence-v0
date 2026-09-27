import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowRight, Play, Droplets, FlaskConical, Sprout, ShieldAlert, Sparkles, Mic } from 'lucide-react'
import GrowingPlant from './GrowingPlant'

const CONVOS = [
  { q: 'Should I irrigate the South Slope?', a: 'Yes, today. Soil moisture fell from 21% to 13.2% this week, below the 18% floor, and the crop is in tuber initiation.', tag: 'Plot B2 · moisture 13.2%' },
  { q: 'Do I need lime on the Hillside Block?', a: 'Yes. pH is 5.1 with aluminium at 1.45 cmol/kg. Lime between seasons to bring it into the 5.5 to 6.5 window.', tag: 'Plot A2 · pH 5.1' },
  { q: 'Any blight risk in East Valley?', a: 'High. Humidity is 92% after 14 mm of rain and NDVI dropped from 0.66 to 0.52. Spray within 24 hours.', tag: 'Plot A3 · blight HIGH' },
]

function ChatDemo() {
  const [i, setI] = useState(0)
  const [phase, setPhase] = useState(0) // 0 question, 1 typing, 2 answer
  useEffect(() => {
    const t = [setTimeout(() => setPhase(1), 1300), setTimeout(() => setPhase(2), 2600), setTimeout(() => { setPhase(0); setI((x) => (x + 1) % CONVOS.length) }, 8200)]
    return () => t.forEach(clearTimeout)
  }, [i])
  const c = CONVOS[i]
  return (
    <div className="hero-chat glass">
      <div className="hc-head">
        <span className="hc-av"><Sparkles size={14} /></span>
        <div><b>Farm advisor</b><span>grounded in your plot's data</span></div>
        <span className="chip" style={{ marginLeft: 'auto' }}><span className="live-dot" />online</span>
      </div>
      <AnimatePresence mode="wait">
        <motion.div key={i} className="hc-body" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <motion.div className="hc-q" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>{c.q}</motion.div>
          {phase === 1 && <div className="hc-typing"><i /><i /><i /></div>}
          {phase === 2 && (
            <motion.div className="hc-a" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
              {c.a}
              <span className="hc-tag">{c.tag}</span>
            </motion.div>
          )}
        </motion.div>
      </AnimatePresence>
      <div className="hc-input"><Mic size={15} /><span>Ask your farm anything…</span></div>
    </div>
  )
}

const CHIPS = [
  { icon: FlaskConical, label: 'Soil pH', v: '6.1', note: 'optimal', cls: '', style: { top: '15%', left: '52%' }, d: 0.9 },
  { icon: Droplets, label: 'Moisture', v: '13.2%', note: 'irrigate', cls: 'amber', style: { top: '37%', right: '4%' }, d: 1.1 },
  { icon: Sprout, label: 'NDVI', v: '0.74', note: 'vigorous', cls: '', style: { top: '31%', left: '61%' }, d: 1.3 },
  { icon: ShieldAlert, label: 'Blight risk', v: 'HIGH', note: 'spray 24h', cls: 'red', style: { top: '12%', right: '8%' }, d: 1.5 },
]

export default function Hero({ onPlay }) {
  return (
    <section className="hero noise">
      <div className="hero-img">
        <img src="/images/farmer-field.jpg" alt="A farmer inspecting his crop in a green field" fetchPriority="high" />
      </div>
      <div className="hero-glow" />
      <GrowingPlant className="hero-plant" />
      {CHIPS.map((c) => (
        <motion.div key={c.label} className={`data-chip ${c.cls}`} style={c.style}
          initial={{ opacity: 0, scale: 0.8, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} transition={{ delay: c.d, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}>
          <c.icon size={16} />
          <div><span>{c.label}</span><b>{c.v}</b></div>
          <em>{c.note}</em>
        </motion.div>
      ))}
      <div className="container hero-inner">
        <motion.div className="hero-copy" initial="h" animate="s" variants={{ s: { transition: { staggerChildren: 0.12 } } }}>
          <motion.span className="eyebrow" variants={fade}>GoMyCode × NVIDIA Hackathon 2026</motion.span>
          <motion.h1 className="h1" variants={fade}>Your farm, digitized.<br /><span className="grad-text">And able to talk back.</span></motion.h1>
          <motion.p className="lead" variants={fade}>
            One 3D digital twin that joins soil chemistry, weather and crop signals for every plot.
            Click a plot, see its intelligence, and ask it anything in plain language.
          </motion.p>
          <motion.div className="hero-ctas" variants={fade}>
            <Link to="/twin" className="btn btn-primary">Open the farm <ArrowRight size={18} className="arrow" /></Link>
            <button className="btn btn-ghost" onClick={onPlay}><Play size={16} /> Watch the 3D scan</button>
          </motion.div>
          <motion.div className="hero-trust" variants={fade}>
            <span><b>OpenUSD</b> digital twin</span>
            <span><b>NVIDIA</b> Omniverse-ready</span>
            <span><b>Nemotron</b> field advisor</span>
          </motion.div>
        </motion.div>
        <motion.div className="hero-chat-wrap" initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7, duration: 1, ease: [0.22, 1, 0.36, 1] }}>
          <ChatDemo />
        </motion.div>
      </div>
      <div className="scroll-cue"><span /></div>
    </section>
  )
}
const fade = { h: { opacity: 0, y: 26 }, s: { opacity: 1, y: 0, transition: { duration: 0.9, ease: [0.22, 1, 0.36, 1] } } }
