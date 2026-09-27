import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, Check, X, MessageCircle, Radio, Cpu, ScanLine, ShieldCheck, FlaskConical, Boxes, MessagesSquare } from 'lucide-react'
import Reveal from '../Reveal'

const ROWS = [
  ['Charts you have to interpret', 'A farm you talk to'],
  ['Flat maps', 'An interactive 3D twin, plot by plot'],
  ['Data stuck in one silo', 'One ingestion layer around the whole farm'],
  ['Answers need an analyst', 'Insights processed, then delivered in chat'],
  ['Closed formats', 'OpenUSD, NVIDIA Omniverse ecosystem, RTX-ready'],
]

export function Compare() {
  return (
    <section className="section compare">
      <div className="container">
        <div className="sec-head center">
          <Reveal><span className="eyebrow">Why we are different</span></Reveal>
          <Reveal delay={0.08}><h2 className="h2">Dashboards show data.<br /><span className="grad-text">We give answers.</span></h2></Reveal>
        </div>
        <Reveal className="cmp card">
          <div className="cmp-head"><span>Conventional farm dashboards</span><span className="accent">Omniverse Crop Intelligence</span></div>
          {ROWS.map(([a, b], i) => (
            <motion.div key={a} className="cmp-row" initial={{ opacity: 0, x: -12 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.08 }}>
              <span className="cmp-a"><X size={16} />{a}</span>
              <span className="cmp-b"><Check size={16} />{b}</span>
            </motion.div>
          ))}
        </Reveal>
      </div>
    </section>
  )
}

const TRUTH = [
  { icon: FlaskConical, t: 'Synthetic demo values on a real schema', d: 'Every plot number is demo data keyed by the real OpenUSD attribute names. No sensor bluffing.' },
  { icon: ScanLine, t: 'Public-capture scan, not our farm yet', d: 'The 3D scan is a public reference capture that proves the pipeline. A real field scan is next.' },
  { icon: MessagesSquare, t: 'The chat is real', d: 'A free-tier NVIDIA Nemotron model answers from the demo farm data. The data is synthetic; the conversation is not.' },
]
export function Honesty() {
  return (
    <section id="honesty" className="section honesty">
      <div className="container">
        <div className="hon card">
          <div className="hon-left">
            <ShieldCheck size={34} className="accent" />
            <h2 className="h2" style={{ fontSize: 'clamp(28px,3.2vw,40px)' }}>Trust is the pitch.</h2>
            <p className="muted">What you see today, labelled truthfully. Every number on screen traces to its source.</p>
          </div>
          <div className="hon-items">
            {TRUTH.map((x, i) => (
              <Reveal key={x.t} delay={i * 0.1} className="hon-item">
                <x.icon size={20} className="accent" />
                <div><b>{x.t}</b><p className="muted">{x.d}</p></div>
              </Reveal>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

const ROAD = [
  { icon: MessageCircle, t: 'Messaging platforms', d: 'The same conversational layer on WhatsApp and SMS, where farmers already are.', tag: 'Next' },
  { icon: Radio, t: 'Live ingestion', d: 'Real soil, weather and crop signals flowing through the ingestion layer via AWS IoT.', tag: 'Phase 2' },
  { icon: Cpu, t: 'Processing models', d: 'SUBSTOR yield and SimCast blight engines behind the insights, as daily services.', tag: 'Phase 2' },
  { icon: Boxes, t: 'Real farm capture', d: 'A scanned field replaces the reference scene; full Omniverse Kit / RTX runtime.', tag: 'Phase 3' },
]
export function Roadmap() {
  return (
    <section id="roadmap" className="section roadmap">
      <div className="container">
        <div className="sec-head">
          <Reveal><span className="eyebrow">Roadmap</span></Reveal>
          <Reveal delay={0.08}><h2 className="h2">From demo twin to every farmer’s phone.</h2></Reveal>
        </div>
        <div className="road">
          <div className="road-line"><motion.i initial={{ scaleX: 0 }} whileInView={{ scaleX: 1 }} viewport={{ once: true }} transition={{ duration: 1.6, ease: [0.22, 1, 0.36, 1] }} /></div>
          {ROAD.map((r, i) => (
            <Reveal key={r.t} delay={0.2 + i * 0.15} className="road-item">
              <span className="road-dot"><r.icon size={18} /></span>
              <span className="chip gray">{r.tag}</span>
              <h3 className="h3">{r.t}</h3>
              <p className="muted">{r.d}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}

export function FinalCTA() {
  return (
    <section className="final noise">
      <img src="/images/sprout2.jpg" alt="" className="final-bg" loading="lazy" />
      <div className="container final-inner">
        <Reveal><h2 className="h1" style={{ fontSize: 'clamp(40px,6vw,76px)' }}>Stop reading dashboards.<br /><span className="grad-text">Start talking to your farm.</span></h2></Reveal>
        <Reveal delay={0.12}><p className="lead" style={{ margin: '24px auto 0' }}>Runs in any browser. No login. Click a plot. Ask it anything.</p></Reveal>
        <Reveal delay={0.2}><Link to="/twin" className="btn btn-primary" style={{ marginTop: 36, height: 60, padding: '0 34px', fontSize: 17 }}>Open the farm <ArrowRight size={20} className="arrow" /></Link></Reveal>
      </div>
    </section>
  )
}
