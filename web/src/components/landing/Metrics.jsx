import Reveal from '../Reveal'

const ITEMS = [
  { k: 'pH', v: '5.5–6.5', t: 'Soil acidity', d: 'Acidity against the potato optimum; below 5.5 the twin suggests lime.', a: 'farmSensor:soilPH' },
  { k: 'NDVI', v: '0 → 1', t: 'Canopy greenness', d: 'Satellite canopy health; a falling NDVI during bulking flags stress.', a: 'farmZone:ndvi' },
  { k: 'GDD', v: 'base 8°C', t: 'Heat units', d: 'Accumulated heat since planting, which drives the growth stage.', a: 'farmZone:accumulatedGDD' },
  { k: 'H₂O', v: '18–34%', t: 'Soil moisture', d: 'Volumetric water content: the irrigation trigger.', a: 'farmSensor:soilMoisture' },
  { k: 'NPK', v: '+ OC', t: 'Fertility', d: 'Nitrogen, phosphorus, potassium and organic carbon drive the fertiliser call.', a: 'farmSensor:nitrogenLevel' },
  { k: 'RISK', v: 'none → severe', t: 'Blight pressure', d: 'Weather-driven late-blight risk with a spray recommendation.', a: 'cropModel:simcastBlightRisk' },
]

export default function Metrics() {
  return (
    <section className="section metrics" style={{ paddingTop: 40 }}>
      <div className="container">
        <div className="sec-head">
          <Reveal><span className="eyebrow">The intelligence grid</span></Reveal>
          <Reveal delay={0.08}><h2 className="h2">Every metric, per plot.</h2></Reveal>
        </div>
        <div className="metric-grid">
          {ITEMS.map((m, i) => (
            <Reveal key={m.k} delay={(i % 3) * 0.08} className="metric card">
              <div className="metric-k">{m.k}</div>
              <div className="metric-v">{m.v}</div>
              <h3 className="h3">{m.t}</h3>
              <p className="muted">{m.d}</p>
              <code>{m.a}</code>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}
