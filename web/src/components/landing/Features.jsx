import { FlaskConical, Sprout, Tractor, ShieldAlert, Cpu, Sparkles, Droplets } from 'lucide-react'
import Reveal from '../Reveal'
import Sparkline from '../../twin/Sparkline'

function PhMini() {
  return (
    <div className="ph-mini">
      <div className="ph-mini-track"><i className="opt" /><i className="mk" style={{ left: '20%' }} /><i className="mk ok" style={{ left: '53%' }} /></div>
      <div className="ph-mini-lbl"><span>A2 · <b className="amber">5.1</b></span><span>A1 · <b className="accent">6.1</b></span></div>
    </div>
  )
}

export default function Features() {
  return (
    <section id="features" className="section features">
      <div className="container">
        <div className="sec-head">
          <Reveal><span className="eyebrow">What the twin knows</span></Reveal>
          <Reveal delay={0.08}><h2 className="h2">Every plot, fully understood.</h2></Reveal>
          <Reveal delay={0.16}><p className="lead">Six kinds of intelligence per plot, all on one OpenUSD schema so a real sensor can drop in without renaming a thing.</p></Reveal>
        </div>
        <div className="bento">
          <Reveal className="b-card b-chat">
            <div className="b-img"><img src="/images/farmer-field.jpg" alt="" loading="lazy" /></div>
            <div className="b-content">
              <span className="b-icon"><Sparkles size={20} /></span>
              <h3 className="h3">AI Field Chat</h3>
              <p className="muted">Every plot is a conversation. Ask by typing or by voice; a real language model answers from that plot’s numbers, and shows its sources.</p>
              <div className="b-bubbles">
                <div className="bb q">What should I apply this week?</div>
                <div className="bb a">P is 9 ppm and K 0.29 on the Hillside Block. Lime first, then DAP at next planting.</div>
              </div>
            </div>
          </Reveal>
          <Reveal className="b-card" delay={0.08}>
            <span className="b-icon"><Droplets size={20} /></span>
            <h3 className="h3">Soil Intelligence</h3>
            <p className="muted">Moisture, EC, organic carbon, N-P-K, aluminium and texture, per plot.</p>
            <div className="b-spark"><Sparkline data={[21, 19.4, 17.9, 16.5, 15.2, 14.1, 13.2]} color="#fbbf24" w={260} h={46} /><span>moisture 21% → 13.2% · irrigate</span></div>
          </Reveal>
          <Reveal className="b-card" delay={0.16}>
            <span className="b-icon"><FlaskConical size={20} /></span>
            <h3 className="h3">pH & Chemistry Alerts</h3>
            <p className="muted">Plot-level pH tracked against the crop’s optimum window.</p>
            <PhMini />
          </Reveal>
          <Reveal className="b-card" delay={0.08}>
            <span className="b-icon"><Sprout size={20} /></span>
            <h3 className="h3">Crop Monitoring</h3>
            <p className="muted">Canopy health (NDVI/EVI), growth stage, heat units and days after planting.</p>
            <div className="b-spark"><Sparkline data={[0.69, 0.7, 0.71, 0.72, 0.72, 0.73, 0.74]} w={260} h={46} /><span>NDVI 0.74 · vigorous canopy</span></div>
          </Reveal>
          <Reveal className="b-card" delay={0.16}>
            <span className="b-icon"><Tractor size={20} /></span>
            <h3 className="h3">Agronomic Data</h3>
            <p className="muted">Variety, planting date, area, yield outlook and spray guidance.</p>
            <div className="b-row"><span>Shangi</span><span>1.8 ha</span><span>31.5 t/ha</span></div>
          </Reveal>
          <Reveal className="b-card" delay={0.24}>
            <span className="b-icon"><Cpu size={20} /></span>
            <h3 className="h3">Processing Insights</h3>
            <p className="muted">Stress, risk and irrigation flags computed from the raw signals.</p>
            <div className="b-flags"><span className="chip amber">irrigate</span><span className="chip amber">lime</span><span className="chip red"><ShieldAlert size={12} />spray 24h</span></div>
          </Reveal>
        </div>
      </div>
    </section>
  )
}
