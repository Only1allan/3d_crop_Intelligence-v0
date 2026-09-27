import { Component, useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { ArrowLeft, Home, Layers, Box, MousePointerClick, MessageSquareText, BarChart3 } from 'lucide-react'
import FarmScene from '../three/FarmScene'
import { ZonePanel, FarmOverview } from '../twin/ZonePanel'
import ChatPanel from '../twin/ChatPanel'
import Logo from '../components/Logo'
import { ZONES, zoneById } from '../data/zones'
import { LAYERS, STATUS_LABEL } from '../lib/status'
import '../twin/twin.css'

class GLBoundary extends Component {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  render() {
    if (this.state.failed) return (
      <div className="gl-fallback">
        <img src="/images/aerial-farm.jpg" alt="Aerial view of farm plots" />
        <div><b>3D is unavailable on this device.</b> Pick a plot from the list; the data and the AI advisor still work.</div>
      </div>
    )
    return this.props.children
  }
}

function webglOk() {
  try { const c = document.createElement('canvas'); return !!(c.getContext('webgl2') || c.getContext('webgl')) } catch { return false }
}

export default function Twin() {
  const [selected, setSelected] = useState(null)
  const [hovered, setHovered] = useState(null)
  const [layer, setLayer] = useState('status')
  const [ready, setReady] = useState(false)
  const [home, setHome] = useState(0)
  const [sheet, setSheet] = useState('insights')
  const [gl] = useState(webglOk)
  const zone = selected ? zoneById(selected) : null

  const select = useCallback((id) => { setSelected(id); if (id) setSheet('insights') }, [])

  useEffect(() => {
    const on = (e) => {
      if (e.key === 'Escape') setSelected(null)
      if (e.target.tagName === 'INPUT') return
      const n = parseInt(e.key, 10)
      if (n >= 1 && n <= ZONES.length) setSelected(ZONES[n - 1].zoneId)
    }
    window.addEventListener('keydown', on)
    return () => window.removeEventListener('keydown', on)
  }, [])
  useEffect(() => { document.title = zone ? `${zone.zoneId} ${zone.displayName} · Live twin` : 'Live 3D twin · Crop Intelligence' }, [zone])

  return (
    <div className="twin">
      <div className="twin-canvas">
        {gl ? (
          <GLBoundary>
            <FarmScene selected={selected} hovered={hovered} layer={layer} homeSignal={home}
              onHover={setHovered} onSelect={select} onReady={() => setTimeout(() => setReady(true), 400)} />
          </GLBoundary>
        ) : <GLBoundary><ThrowGL /></GLBoundary>}
        <AnimatePresence>
          {!ready && gl && (
            <motion.div className="twin-splash" initial={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.8 }}>
              <div className="spinner" /><b>Composing the farm twin</b><span>plots · probes · weather hub · crop canopy</span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <header className="twin-top">
        <Link to="/" className="twin-logo" aria-label="Back to home"><ArrowLeft size={16} /><Logo /></Link>
        <div className="twin-badges">
          <span className="chip"><span className="live-dot" />Live twin</span>
          <span className="chip amber">Demo · synthetic values on the real schema</span>
        </div>
        <div className="twin-links">
          <Link to="/lab" className="btn btn-ghost btn-sm"><Box size={15} />Real 3D data</Link>
        </div>
      </header>

      <aside className="twin-left glass">
        <div className="tl-title">Plots</div>
        <ul className="zone-list" role="listbox" aria-label="Farm plots">
          {ZONES.map((z, i) => (
            <li key={z.zoneId}>
              <button role="option" aria-selected={selected === z.zoneId}
                className={`zone-item ${selected === z.zoneId ? 'on' : ''} ${hovered === z.zoneId ? 'hov' : ''}`}
                onMouseEnter={() => setHovered(z.zoneId)} onMouseLeave={() => setHovered(null)}
                onClick={() => select(selected === z.zoneId ? null : z.zoneId)}>
                <span className={`dot ${z.status}`} />
                <span className="zi-id">{z.zoneId}</span>
                <span className="zi-name">{z.displayName}<small>{STATUS_LABEL[z.status]}</small></span>
                <kbd>{i + 1}</kbd>
              </button>
            </li>
          ))}
        </ul>
        <div className="tl-title" style={{ marginTop: 14 }}><Layers size={13} /> Data layer</div>
        <div className="layer-seg">
          {Object.entries(LAYERS).map(([k, l]) => (
            <button key={k} className={layer === k ? 'on' : ''} onClick={() => setLayer(k)}>{l.label}</button>
          ))}
        </div>
        {LAYERS[layer].stops ? (
          <div className="legend">
            <i style={{ background: `linear-gradient(90deg, ${LAYERS[layer].stops.join(',')})` }} />
            <div><span>{LAYERS[layer].legend[0]}</span><span>{LAYERS[layer].legend[1]}</span></div>
          </div>
        ) : (
          <div className="legend-status">
            {['nominal', 'warning', 'critical', 'offline'].map((s) => <span key={s}><span className={`dot ${s}`} />{STATUS_LABEL[s]}</span>)}
          </div>
        )}
        <button className="btn btn-ghost btn-sm reset" onClick={() => { setSelected(null); setHome((h) => h + 1) }}><Home size={14} />Reset view</button>
      </aside>

      <aside className={`twin-right glass sheet-${sheet}`}>
        <div className="sheet-tabs">
          <button className={sheet === 'insights' ? 'on' : ''} onClick={() => setSheet('insights')}><BarChart3 size={15} />Insights</button>
          <button className={sheet === 'chat' ? 'on' : ''} onClick={() => setSheet('chat')}><MessageSquareText size={15} />Ask AI</button>
        </div>
        <div className="tr-insights">
          <AnimatePresence mode="wait">
            <motion.div key={selected || 'farm'} initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -16 }} transition={{ duration: 0.3 }} style={{ height: '100%' }}>
              {zone ? <ZonePanel zone={zone} onClose={() => setSelected(null)} /> : <FarmOverview onSelect={select} />}
            </motion.div>
          </AnimatePresence>
        </div>
        <div className="tr-chat"><ChatPanel zone={zone} /></div>
      </aside>

      <AnimatePresence>
        {!selected && ready && (
          <motion.div className="twin-hint" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            <MousePointerClick size={16} className="accent" />
            <span><b>Click a plot</b> to inspect it and talk to it · drag to orbit · scroll to zoom · keys 1–6 · Esc resets</span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function ThrowGL() { throw new Error('no webgl') }
