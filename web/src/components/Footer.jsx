import { Link } from 'react-router-dom'
import Logo from './Logo'

export default function Footer() {
  return (
    <footer style={{ borderTop: '1px solid var(--line)', padding: '56px 0 40px', background: '#000' }}>
      <div className="container" style={{ display: 'grid', gap: 28 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 24, flexWrap: 'wrap' }}>
          <div style={{ maxWidth: 420 }}>
            <Logo />
            <p className="muted" style={{ fontSize: 14, marginTop: 14 }}>
              A 3D digital twin of the farm on OpenUSD, built for NVIDIA Omniverse, that farmers can talk to.
              GoMyCode × NVIDIA Hackathon 2026.
            </p>
          </div>
          <div style={{ display: 'flex', gap: 40, fontSize: 14, flexWrap: 'wrap' }}>
            <div style={{ display: 'grid', gap: 8 }}>
              <b style={{ fontWeight: 600 }}>Product</b>
              <Link className="muted" to="/twin">Live 3D twin</Link>
              <Link className="muted" to="/lab">Real 3D data</Link>
              <Link className="muted" to="/#roadmap">Roadmap</Link>
            </div>
            <div style={{ display: 'grid', gap: 8 }}>
              <b style={{ fontWeight: 600 }}>About</b>
              <Link className="muted" to="/#honesty">What's real</Link>
              <Link className="muted" to="/credits">Image credits</Link>
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap', fontSize: 13, color: 'var(--text-3)', borderTop: '1px solid var(--line)', paddingTop: 22 }}>
          <span><span className="dot nominal" style={{ marginRight: 8 }} />Demo values on a real schema. No live sensors yet.</span>
          <span>Photos: Unsplash License · 3D plant scans: Pheno4D (PLoS ONE 2021)</span>
        </div>
      </div>
    </footer>
  )
}
