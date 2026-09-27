import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Database, Cpu, MessagesSquare, MousePointerClick, BarChart3, MessageCircleQuestion, ArrowRight, Radio, Leaf, Layers3 } from 'lucide-react'
import Reveal from '../Reveal'

const FarmScene = lazy(() => import('../../three/FarmScene'))

const LAYERS = [
  { n: '01', icon: Database, t: 'Ingestion', d: 'The farm itself, every plot in 3D, plus the data points around it: soil chemistry, pH, weather and crop signals.', tags: ['Soil probes', 'Weather hub', 'Satellite NDVI'] },
  { n: '02', icon: Cpu, t: 'Processing', d: 'Raw data becomes insight: crop health, stress and risk flags, growth stage and a yield outlook for every plot.', tags: ['pH bands', 'Irrigation flags', 'Blight risk'] },
  { n: '03', icon: MessagesSquare, t: 'Communication', d: 'The farmer talks to those insights. A chatbot today; WhatsApp and SMS next, same brain wherever the farmer already talks.', tags: ['AI field chat', 'Voice', 'Messaging (next)'] },
]
const STEPS = [
  { icon: MousePointerClick, t: 'Click a plot', d: 'Every plot of the 3D twin is selectable.' },
  { icon: BarChart3, t: 'See its intelligence', d: 'Soil, pH, crop and agronomy on one card.' },
  { icon: MessageCircleQuestion, t: 'Ask it anything', d: 'A real LLM answers with that plot’s numbers.' },
]

function useInView(ref) {
  const [v, setV] = useState(false)
  useEffect(() => {
    const io = new IntersectionObserver(([e]) => setV(e.isIntersecting), { rootMargin: '0px' })
    ref.current && io.observe(ref.current)
    return () => io.disconnect()
  }, [ref])
  return v
}

export default function Solution() {
  const box = useRef(null)
  const inView = useInView(box)
  const [mounted, setMounted] = useState(false)
  useEffect(() => { if (inView) setMounted(true) }, [inView])
  return (
    <section id="solution" className="section solution">
      <div className="sol-bg"><img src="/images/aerial-farm.jpg" alt="" loading="lazy" /></div>
      <div className="container">
        <div className="sec-head center">
          <Reveal><span className="eyebrow">Our solution</span></Reveal>
          <Reveal delay={0.08}><h2 className="h2">One digital twin of the farm.<br /><span className="grad-text">Built in three layers.</span></h2></Reveal>
          <Reveal delay={0.16}><p className="lead" style={{ margin: '22px auto 0' }}>Ask a question in plain language. Get an answer grounded in <i>your</i> farm’s numbers.</p></Reveal>
        </div>

        <div className="layers">
          {LAYERS.map((l, i) => (
            <Reveal key={l.t} delay={i * 0.15} className="layer card">
              <div className="layer-top"><span className="layer-n">{l.n}</span><span className="layer-icon"><l.icon size={22} /></span></div>
              <h3 className="h3">{l.t}</h3>
              <p className="muted">{l.d}</p>
              <div className="layer-tags">{l.tags.map((t) => <span key={t} className="chip gray">{t}</span>)}</div>
              {i < 2 && <div className="flow" aria-hidden="true"><i /><i /><i /></div>}
            </Reveal>
          ))}
        </div>

        <Reveal className="preview" style={{ marginTop: 72 }}>
          <div className="preview-frame" ref={box}>
            {mounted ? (
              <Suspense fallback={<div className="preview-ph" />}>
                <FarmScene interactive={false} autoRotate showLabels paused={!inView} maxDpr={1.5} />
              </Suspense>
            ) : <div className="preview-ph" />}
            <div className="preview-overlay">
              <div className="po-top">
                <span className="chip"><span className="live-dot" />Live 3D twin · rendered in your browser</span>
                <div className="po-legend">
                  <span><Radio size={13} />soil probes stream to the weather hub</span>
                  <span><Leaf size={13} />crop colour follows NDVI</span>
                  <span><Layers3 size={13} />pulsing plots need attention</span>
                </div>
              </div>
              <Link to="/twin" className="btn btn-primary po-cta">Open the live twin <ArrowRight size={18} className="arrow" /></Link>
            </div>
          </div>
        </Reveal>

        <div className="steps">
          {STEPS.map((s, i) => (
            <Reveal key={s.t} delay={i * 0.12} className="step">
              <span className="step-n">{i + 1}</span>
              <s.icon size={22} className="accent" />
              <div><b>{s.t}</b><span>{s.d}</span></div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}
