const WORDS = ['Soil pH', 'NDVI', 'Soil moisture', 'Growing degree days', 'Nitrogen', 'Phosphorus', 'Potassium', 'Organic carbon', 'Blight risk', 'Growth stage', 'Yield outlook', 'Electrical conductivity']
export default function Marquee() {
  const row = [...WORDS, ...WORDS]
  return (
    <div className="marquee" aria-hidden="true">
      <div className="marquee-track">
        {row.map((w, i) => <span key={i}>{w}<i>✦</i></span>)}
      </div>
    </div>
  )
}
