import { motion } from 'framer-motion'
import { Droplets, FlaskConical, Bug, FileSpreadsheet, CloudSun, NotebookPen, Satellite } from 'lucide-react'
import Reveal from '../Reveal'

const QUESTIONS = [
  { icon: Droplets, q: 'Irrigate or not?', d: 'Water is pumped on habit, not on what the soil actually holds.' },
  { icon: FlaskConical, q: 'Lime or not?', d: 'Soil pH is tested once, filed away, and never linked to the plot again.' },
  { icon: Bug, q: 'Spray or not?', d: 'Blight weather is spotted after the canopy has already started to die.' },
]
const STATS = [
  { v: '40%', l: 'of global crop production is lost to plant pests and diseases every year', s: 'FAO, 2019' },
  { v: '70%', l: 'of the world’s freshwater withdrawals go to agriculture', s: 'FAO AQUASTAT' },
  { v: '1/3', l: 'of the world’s food is grown on small farms with the least access to tools', s: 'FAO, 2021' },
]
const SHARDS = [
  { icon: FileSpreadsheet, t: 'Soil lab PDF', s: 'pH 5.1 · filed in 2024', x: -150, y: -90, r: -8 },
  { icon: CloudSun, t: 'Weather app', s: '92% humidity, no alert', x: 160, y: -60, r: 7 },
  { icon: NotebookPen, t: 'Field notebook', s: '“leaves look yellow?”', x: -120, y: 110, r: 6 },
  { icon: Satellite, t: 'Satellite portal', s: 'NDVI tile, never opened', x: 150, y: 120, r: -6 },
]

export default function Problem() {
  return (
    <section id="problem" className="section problem">
      <div className="container">
        <div className="sec-head">
          <Reveal><span className="eyebrow">The problem</span></Reveal>
          <Reveal delay={0.08}><h2 className="h2">Farmers lack crop monitoring tools.<br /><span className="muted">So the calls that decide a season are made blind.</span></h2></Reveal>
        </div>

        <div className="problem-grid">
          <div className="problem-photos">
            <Reveal className="pp pp-1"><img src="/images/woman-planting.jpg" alt="A woman planting seedlings in a field" loading="lazy" /></Reveal>
            <Reveal className="pp pp-2" delay={0.15}><img src="/images/carrying-toddler.jpg" alt="Farmers working a plot by hand" loading="lazy" /></Reveal>
            <Reveal className="pp pp-3" delay={0.3}><img src="/images/grass-bundle.jpg" alt="A farmer carrying a bundle of harvested crop" loading="lazy" /></Reveal>
            <div className="pp-badge glass"><span className="dot warning" />No single view of the farm</div>
          </div>
          <div className="problem-qs">
            {QUESTIONS.map((x, i) => (
              <Reveal key={x.q} delay={i * 0.1} className="pq card">
                <span className="pq-icon"><x.icon size={20} /></span>
                <div><h3 className="h3">{x.q}</h3><p className="muted">{x.d}</p></div>
                <span className="pq-mark">?</span>
              </Reveal>
            ))}
            <Reveal delay={0.3}>
              <p className="problem-note">The cost is wasted water, wasted inputs and crop loss that could have been prevented.</p>
            </Reveal>
          </div>
        </div>

        <div className="scatter-wrap">
          <Reveal className="scatter-copy">
            <h3 className="h3" style={{ fontSize: 28 }}>The data exists. <span className="accent">In fragments.</span></h3>
            <p className="muted">Soil readings here, weather there, crop observations somewhere else: scattered, late, or never collected. No way to <b style={{ color: '#fff' }}>ask</b> the farm a question and get an answer today.</p>
          </Reveal>
          <div className="scatter">
            <div className="scatter-core"><span>?</span></div>
            {SHARDS.map((s, i) => (
              <motion.div key={s.t} className="shard glass"
                initial={{ x: 0, y: 0, opacity: 0, rotate: 0 }}
                whileInView={{ x: s.x, y: s.y, opacity: 1, rotate: s.r }}
                viewport={{ once: true, margin: '-100px' }}
                transition={{ delay: 0.2 + i * 0.12, duration: 1.1, ease: [0.22, 1, 0.36, 1] }}>
                <s.icon size={18} className="accent" />
                <div><b>{s.t}</b><span>{s.s}</span></div>
              </motion.div>
            ))}
          </div>
        </div>

        <div className="stats">
          {STATS.map((s, i) => (
            <Reveal key={s.v} delay={i * 0.1} className="stat">
              <div className="stat-v grad-text">{s.v}</div>
              <p>{s.l}</p>
              <span>{s.s}</span>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}
