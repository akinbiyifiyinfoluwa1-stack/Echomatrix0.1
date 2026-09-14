import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Activity, BrainCircuit, ChartNoAxesCombined, ChevronRight, CircleHelp, Database, FlaskConical, Gauge, Layers3, Menu, Network, Play, RefreshCw, ShieldCheck, SlidersHorizontal, Sparkles, TerminalSquare, Zap } from 'lucide-react'
import './styles.css'

type BrainStatus = {
  status?: string
  memory_size?: number
  durable_memory?: boolean
  real_money_execution?: boolean
  advanced_capabilities?: number
  validation_layer?: boolean
  robustness_layer?: boolean
}

type NavKey = 'Dashboard' | 'Research' | 'Simulations' | 'Data Pipeline' | 'Models' | 'Market Intel' | 'Alerts' | 'System Controls' | 'Docs'

const API_BASE = (import.meta.env.VITE_BRAIN_API_URL || '').replace(/\/$/, '')

const nav: Array<{ label: NavKey; icon: React.ReactNode }> = [
  { label: 'Dashboard', icon: <Gauge size={17} /> },
  { label: 'Research', icon: <FlaskConical size={17} /> },
  { label: 'Simulations', icon: <Play size={17} /> },
  { label: 'Data Pipeline', icon: <Database size={17} /> },
  { label: 'Models', icon: <BrainCircuit size={17} /> },
  { label: 'Market Intel', icon: <ChartNoAxesCombined size={17} /> },
  { label: 'Alerts', icon: <Activity size={17} /> },
]

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`)
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`)
  return response.json() as Promise<T>
}

function App() {
  const [active, setActive] = useState<NavKey>('Dashboard')
  const [status, setStatus] = useState<BrainStatus>({})
  const [connected, setConnected] = useState(false)
  const [loading, setLoading] = useState(false)
  const [lastRefresh, setLastRefresh] = useState('—')

  const refresh = async () => {
    setLoading(true)
    try {
      const data = await getJson<BrainStatus>('/brain/status')
      setStatus(data)
      setConnected(true)
      setLastRefresh(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }))
    } catch {
      setConnected(false)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { refresh() }, [])

  const cards = useMemo(() => [
    { label: 'Data Throughput', value: '—', delta: 'Awaiting live telemetry', icon: <Database /> },
    { label: 'Active Simulations', value: '—', delta: 'Simulation engine ready', icon: <Play /> },
    { label: 'GPU Utilization', value: '—', delta: 'Telemetry not exposed', icon: <Zap /> },
    { label: 'Validation Pass Rate', value: status.validation_layer ? 'READY' : '—', delta: 'Research gate', icon: <ShieldCheck /> },
  ], [status.validation_layer])

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Sparkles size={19} /></div>
          <div><strong>EchoMatrix</strong><span>Control Console</span></div>
        </div>

        <div className="workspace-label">WORKSPACE</div>
        <nav>
          {nav.map(item => (
            <button key={item.label} className={active === item.label ? 'nav-item active' : 'nav-item'} onClick={() => setActive(item.label)}>
              {item.icon}<span>{item.label}</span>{active === item.label && <ChevronRight className="nav-chevron" size={14} />}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <button className="nav-item" onClick={() => setActive('System Controls')}><SlidersHorizontal size={17} /><span>System Controls</span></button>
          <button className="nav-item" onClick={() => setActive('Docs')}><CircleHelp size={17} /><span>Docs</span></button>
          <div className="mode-chip"><span className="dot green" /> Simulation-only mode</div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="topbar-left"><Menu size={18} /><span className="breadcrumb">{active}</span></div>
          <div className="topbar-right">
            <span className={connected ? 'connection connected' : 'connection'}><span className="dot" /> {connected ? 'Brain connected' : 'Brain offline'}</span>
            <span className="refresh-time">Updated {lastRefresh}</span>
            <button className="icon-button" onClick={refresh} disabled={loading} title="Refresh brain status"><RefreshCw size={17} className={loading ? 'spin' : ''} /></button>
          </div>
        </header>

        <section className="content">
          <div className="hero-row">
            <div>
              <div className="eyebrow">ECHOMATRIX / LIVE CONTROL</div>
              <h1>{active === 'Dashboard' ? 'System overview' : active}</h1>
              <p>{active === 'Dashboard' ? 'A live surface for the EchoMatrix research, simulation, validation and intelligence layers.' : 'This surface is wired to the same backend contracts as the brain runtime.'}</p>
            </div>
            <div className="runtime-pill"><span className="dot green" /> Runtime <strong>{status.status || 'unknown'}</strong></div>
          </div>

          {active === 'Dashboard' ? <>
            <div className="metric-grid">
              {cards.map(card => <MetricCard key={card.label} {...card} />)}
            </div>

            <div className="section-grid">
              <Panel title="Brain Status" icon={<BrainCircuit size={17} />}>
                <StatusRow label="Runtime" value={status.status || 'offline'} state={connected ? 'ok' : 'warn'} />
                <StatusRow label="Advanced capabilities" value={String(status.advanced_capabilities ?? '—')} state="ok" />
                <StatusRow label="Validation layer" value={status.validation_layer ? 'enabled' : 'disabled'} state={status.validation_layer ? 'ok' : 'warn'} />
                <StatusRow label="Robustness layer" value={status.robustness_layer ? 'enabled' : 'disabled'} state={status.robustness_layer ? 'ok' : 'warn'} />
                <StatusRow label="Durable memory" value={status.durable_memory ? 'enabled' : '—'} state={status.durable_memory ? 'ok' : 'warn'} />
                <StatusRow label="Real-money execution" value={status.real_money_execution ? 'ENABLED' : 'disabled'} state={status.real_money_execution ? 'bad' : 'ok'} />
              </Panel>

              <Panel title="Research Validation" icon={<FlaskConical size={17} />}>
                <Progress label="Dataset validation" value={status.validation_layer ? 100 : 0} />
                <Progress label="Walk-forward engine" value={status.validation_layer ? 100 : 0} />
                <Progress label="Out-of-sample summary" value={status.validation_layer ? 100 : 0} />
                <div className="panel-note">Research endpoints are ready. Results appear here when experiments are submitted.</div>
              </Panel>

              <Panel title="Robustness / Stress" icon={<ShieldCheck size={17} />}>
                <div className="empty-state"><Network size={23} /><strong>Stress lab ready</strong><span>Stress matrix, Monte Carlo and bounded robustness scoring are available through the brain API.</span></div>
              </Panel>

              <Panel title="Simulation / Portfolio" icon={<Play size={17} />}>
                <div className="empty-state"><TerminalSquare size={23} /><strong>No active run</strong><span>Start a simulation from the API or orchestration layer; this console will become the observation surface.</span></div>
              </Panel>
            </div>

            <div className="bottom-grid">
              <Panel title="System Resource Utilization" icon={<Activity size={17} />} wide>
                <div className="chart-placeholder">
                  <div className="chart-grid" />
                  <div className="chart-line" />
                  <span>Live infrastructure telemetry will populate this chart.</span>
                </div>
              </Panel>
              <Panel title="Current Events" icon={<Layers3 size={17} />}>
                <div className="event"><span className="event-dot cyan" /><div><strong>Brain runtime</strong><small>Connected status is sampled from /brain/status.</small></div></div>
                <div className="event"><span className="event-dot green" /><div><strong>Validation</strong><small>Temporal split, leakage and OOS contracts are present.</small></div></div>
                <div className="event"><span className="event-dot amber" /><div><strong>Telemetry</strong><small>Waiting for service-level resource metrics.</small></div></div>
              </Panel>
            </div>
          </> : <ModuleView title={active} />}
        </section>
      </main>
    </div>
  )
}

function MetricCard({ label, value, delta, icon }: { label: string; value: string; delta: string; icon: React.ReactNode }) {
  return <div className="metric-card"><div className="metric-icon">{icon}</div><span className="metric-label">{label}</span><strong>{value}</strong><small>{delta}</small></div>
}

function Panel({ title, icon, children, wide = false }: { title: string; icon: React.ReactNode; children: React.ReactNode; wide?: boolean }) {
  return <section className={wide ? 'panel wide' : 'panel'}><div className="panel-header"><div>{icon}<strong>{title}</strong></div><button className="more">•••</button></div>{children}</section>
}

function StatusRow({ label, value, state }: { label: string; value: string; state: 'ok' | 'warn' | 'bad' }) {
  return <div className="status-row"><span>{label}</span><span className={`status-value ${state}`}><span className="dot" />{value}</span></div>
}

function Progress({ label, value }: { label: string; value: number }) {
  return <div className="progress-row"><div><span>{label}</span><strong>{value}%</strong></div><div className="progress-track"><div style={{ width: `${value}%` }} /></div></div>
}

function ModuleView({ title }: { title: string }) {
  const descriptions: Record<string, string> = {
    Research: 'Run validation, walk-forward windows, leakage checks and out-of-sample summaries against supplied datasets.',
    Simulations: 'Launch and observe simulation-only replay, stress and autonomous research scenarios.',
    'Data Pipeline': 'Observe normalized market observations and data-quality gates.',
    Models: 'Track provider evaluation, strategy evolution and model-level research outputs.',
    'Market Intel': 'Surface normalized external intelligence and market-state observations.',
    Alerts: 'Review system and research events before they become operational blockers.',
    'System Controls': 'Operational controls will expose safe research toggles, health checks and environment state.',
    Docs: 'Documentation and contracts for the EchoMatrix brain runtime will live here.',
  }
  return <div className="module-placeholder"><div className="module-icon"><BrainCircuit size={28} /></div><h2>{title}</h2><p>{descriptions[title] || 'EchoMatrix module'}</p><div className="module-status"><span className="dot green" /> Connected to dashboard shell <ChevronRight size={15} /></div></div>
}

createRoot(document.getElementById('root')!).render(<App />)
