import React, { useEffect, useState } from 'react'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip, ReferenceArea, ReferenceLine } from 'recharts'
import { Activity, Heart, Mountain, Zap, Clock, Gauge, Upload, RefreshCw, MapPin, X, ChevronRight } from 'lucide-react'
import UploadZone from './components/UploadZone'
import MapView from './components/MapView'

type Run = any

const fmtPace = (p: string | undefined) => p || '--'
const fmtDuration = (d: string | number | undefined) => {
  if (typeof d === 'string') return d
  if (typeof d === 'number') return `${Math.floor(d / 60)}:${String(d % 60).padStart(2, '0')}`
  return '--'
}
const fmtDist = (d: any) => {
  const n = parseFloat(d)
  return isNaN(n) ? '0' : n.toFixed(2)
}
const fmtAscent = (a: any) => {
  const n = parseFloat(a)
  return isNaN(n) ? '0' : Math.round(n)
}

export default function App() {
  const [runs, setRuns] = useState<Run[]>([])
  const [selected, setSelected] = useState<Run | null>(null)
  const [colorBy, setColorBy] = useState<'speed' | 'ele' | 'hr'>('ele')
  const [points, setPoints] = useState<any[]>([])
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [syncing, setSyncing] = useState(false)

  const loadRuns = async () => {
    try {
      const r = await fetch('/api/runs').then(x => x.json())
      setRuns(r)
      if (r[0] && !selected) selectRun(r[0].id)
    } catch {
      const ls = localStorage.getItem('volkov_runs_v1')
      const arr = ls ? JSON.parse(ls) : []
      setRuns(arr)
      if (arr[0]) { setSelected(arr[0]); try { setPoints(JSON.parse(arr[0].points_json || '[]')) } catch {} }
    }
  }

  const selectRun = async (id: any) => {
    let data: any
    if (typeof id === 'object') { data = id } else {
      try { data = await fetch(`/api/runs/${id}`).then(x => x.json()) }
      catch { data = runs.find((r: any) => r.id === id) }
    }
    setSelected(data)
    setSidebarOpen(false)
    try {
      const pts = data.points || JSON.parse(data.points_json || '[]')
      setPoints(pts)
    } catch { setPoints([]) }
  }

  const onUpload = async (f: File) => {
    const fd = new FormData()
    fd.append('file', f)
    try {
      const res = await fetch('/api/upload', { method: 'POST', body: fd })
      const j = await res.json()
      setPoints(j.points || [])
      loadRuns()
      setSelected(j)
    } catch {
      alert('שגיאת העלאה')
    }
  }

  const syncGarmin = async () => {
    setSyncing(true)
    try {
      await fetch('/api/sync/garmin', { method: 'POST' })
      loadRuns()
    } catch {
      alert('שגיאת סנכרון, בדוק .env וטוקן')
    }
    setSyncing(false)
  }

  useEffect(() => { loadRuns() }, [])

  // Identify climb at 12.5-15 min and descent at 16-18 min
  const climbPoints = points.filter(p => p.time_sec / 60 >= 12.5 && p.time_sec / 60 <= 15)
  const descentPoints = points.filter(p => p.time_sec / 60 >= 16 && p.time_sec / 60 <= 18)
  const climbDelta = climbPoints.length > 1 ? climbPoints[climbPoints.length - 1].ele_smooth - climbPoints[0].ele_smooth : 0
  const descentDelta = descentPoints.length > 1 ? descentPoints[descentPoints.length - 1].ele_smooth - descentPoints[0].ele_smooth : 0

  const chartData = points.map(p => ({
    dist: p.dist_km?.toFixed(2),
    time: (p.time_sec / 60).toFixed(1),
    ele: p.ele_smooth || p.ele,
    hr: p.hr,
    speed: p.speed_kmh,
  }))

  const stats = [
    { icon: MapPin, label: 'מרחק', value: `${fmtDist(selected?.distance_km)} ק"מ`, color: 'text-violet-400' },
    { icon: Clock, label: 'זמן', value: fmtDuration(selected?.duration_str || selected?.duration_sec), color: 'text-blue-400' },
    { icon: Gauge, label: 'קצב', value: fmtPace(selected?.avg_pace_min_km), color: 'text-cyan-400' },
    { icon: Heart, label: 'דופק ממוצע', value: selected?.avg_hr || 0, color: 'text-red-400' },
    { icon: Mountain, label: 'עלייה', value: `${fmtAscent(selected?.total_ascent)} מ'`, color: 'text-green-400' },
    { icon: Activity, label: 'רציפה', value: selected?.is_continuous ? 'כן ✓' : 'לא', color: 'text-amber-400' },
  ]

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Header */}
      <header className="border-b border-zinc-800/80 sticky top-0 z-20 bg-zinc-950/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 md:px-6 py-3 flex justify-between items-center">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-blue-500 grid place-items-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-black tracking-tight">Volkov Run Lab</h1>
              <p className="text-[10px] text-zinc-500 -mt-0.5">ניתוח ריצות · Garmin Auto-Sync</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={syncGarmin}
              disabled={syncing}
              className="flex items-center gap-1.5 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white px-3 py-2 rounded-xl text-sm font-medium transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">סנכרן Garmin</span>
            </button>
            <button
              onClick={() => document.getElementById('filein')?.click()}
              className="flex items-center gap-1.5 bg-zinc-800 hover:bg-zinc-700 text-white px-3 py-2 rounded-xl text-sm font-medium transition-colors"
            >
              <Upload className="w-4 h-4" />
              <span className="hidden sm:inline">העלאה</span>
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 md:px-6 py-6 grid grid-cols-12 gap-4">
        {/* Sidebar */}
        <aside className={`col-span-12 md:col-span-3 ${sidebarOpen ? 'fixed inset-0 z-30 md:static bg-zinc-950' : 'hidden md:block'}`}>
          <div className="md:hidden flex justify-between items-center mb-4">
            <h2 className="font-bold">היסטוריה</h2>
            <button onClick={() => setSidebarOpen(false)}><X className="w-5 h-5" /></button>
          </div>
          <UploadZone onUpload={onUpload} />
          <div className="mt-4 bg-zinc-900/80 rounded-2xl p-4 border border-zinc-800">
            <h3 className="font-bold mb-3 text-sm text-zinc-300">היסטוריה ({runs.length})</h3>
            <div className="space-y-2 max-h-[55vh] overflow-auto pr-1">
              {runs.length === 0 && (
                <div className="text-center text-zinc-600 text-sm py-8">אין ריצות עדיין</div>
              )}
              {runs.map((r: any) => (
                <div
                  key={r.id}
                  onClick={() => selectRun(r.id)}
                  className={`p-3 rounded-xl cursor-pointer border transition-all ${selected?.id === r.id
                    ? 'bg-violet-600/20 border-violet-500/50'
                    : 'bg-zinc-800/50 border-zinc-800 hover:border-zinc-700'
                    }`}
                >
                  <div className="font-bold text-sm flex items-center justify-between">
                    <span>{(r.date || '').slice(0, 10) || 'היום'}</span>
                    <span className="text-violet-400">{fmtDist(r.distance_km)} ק"מ</span>
                  </div>
                  <div className="text-xs text-zinc-400 mt-1 flex items-center gap-2">
                    <span>{r.duration_str}</span>
                    <span>·</span>
                    <span>{r.avg_pace_min_km}</span>
                    <span>·</span>
                    <span className="text-red-400">❤ {r.avg_hr}</span>
                    {r.is_continuous ? <span className="bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded-full text-[10px]">רציפה</span> : null}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <section className="col-span-12 md:col-span-9">
          {selected ? (
            <>
              {/* Stats Cards */}
              <div className="grid grid-cols-3 md:grid-cols-6 gap-3 mb-6">
                {stats.map((s, i) => (
                  <div key={i} className="bg-zinc-900/80 rounded-2xl p-4 border border-zinc-800">
                    <div className="flex items-center gap-1.5 mb-1">
                      <s.icon className={`w-4 h-4 ${s.color}`} />
                      <span className="text-[11px] text-zinc-500">{s.label}</span>
                    </div>
                    <div className="font-bold text-lg">{s.value}</div>
                  </div>
                ))}
              </div>

              {/* Color Mode Toggle */}
              <div className="flex gap-2 mb-4">
                {(['speed', 'ele', 'hr'] as const).map(m => (
                  <button
                    key={m}
                    onClick={() => setColorBy(m)}
                    className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${colorBy === m
                      ? 'bg-violet-600 text-white'
                      : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'
                      }`}
                  >
                    {m === 'speed' ? '⚡ מהירות' : m === 'ele' ? '⛰️ גובה' : '❤️ דופק'}
                  </button>
                ))}
              </div>

              {/* Map */}
              <div className="bg-zinc-900/80 rounded-2xl border border-zinc-800 overflow-hidden mb-6">
                <MapView points={points} colorBy={colorBy} />
              </div>

              {/* Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Elevation Chart */}
                <div className="bg-zinc-900/80 rounded-2xl p-5 border border-zinc-800">
                  <h4 className="font-bold mb-3 text-sm text-zinc-300">📈 גובה לפי מרחק</h4>
                  <ResponsiveContainer width="100%" height={200}>
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="eleGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#22c55e" stopOpacity={0.4} />
                          <stop offset="100%" stopColor="#22c55e" stopOpacity={0.05} />
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="dist" tick={{ fill: '#71717a', fontSize: 11 }} axisLine={{ stroke: '#3f3f46' }} />
                      <YAxis tick={{ fill: '#71717a', fontSize: 11 }} axisLine={{ stroke: '#3f3f46' }} domain={['auto', 'auto']} />
                      <Tooltip
                        contentStyle={{ background: '#18181b', border: '1px solid #3f3f46', borderRadius: 12, fontSize: 12 }}
                        labelStyle={{ color: '#a1a1aa' }}
                      />
                      <Area type="monotone" dataKey="ele" stroke="#22c55e" strokeWidth={2} fill="url(#eleGrad)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>

                {/* HR + Speed Chart */}
                <div className="bg-zinc-900/80 rounded-2xl p-5 border border-zinc-800">
                  <h4 className="font-bold mb-3 text-sm text-zinc-300">❤️ דופק ומהירות</h4>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={chartData}>
                      <XAxis dataKey="time" tick={{ fill: '#71717a', fontSize: 11 }} axisLine={{ stroke: '#3f3f46' }} />
                      <YAxis yAxisId="left" tick={{ fill: '#ef4444', fontSize: 11 }} axisLine={{ stroke: '#3f3f46' }} />
                      <YAxis yAxisId="right" orientation="right" tick={{ fill: '#3b82f6', fontSize: 11 }} axisLine={{ stroke: '#3f3f46' }} />
                      <Tooltip
                        contentStyle={{ background: '#18181b', border: '1px solid #3f3f46', borderRadius: 12, fontSize: 12 }}
                        labelStyle={{ color: '#a1a1aa' }}
                      />
                      <Line yAxisId="left" type="monotone" dataKey="hr" stroke="#ef4444" strokeWidth={2} dot={false} name="דופק" />
                      <Line yAxisId="right" type="monotone" dataKey="speed" stroke="#3b82f6" strokeWidth={1.5} strokeDasharray="5 5" dot={false} name="מהירות" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Analysis Card */}
              <div className="mt-6 bg-gradient-to-br from-violet-900/30 to-blue-900/20 border border-violet-500/30 rounded-2xl p-5">
                <h4 className="font-bold mb-2 text-violet-300">🔍 ניתוח חכם</h4>
                <div className="space-y-2 text-sm text-zinc-300">
                  {selected.is_continuous && (
                    <div className="flex items-center gap-2">
                      <span className="text-green-400">✓</span>
                      <span>ריצה רציפה מזוהה (18-45 דק') — ללא הפסקות</span>
                    </div>
                  )}
                  {climbPoints.length > 1 && (
                    <div className="flex items-center gap-2">
                      <span className="text-amber-400">⬆</span>
                      <span>עלייה בדקות 12.5-15: <b className="text-amber-300">{climbDelta.toFixed(1)} מ'</b> — עלייה משמעותית</span>
                    </div>
                  )}
                  {descentPoints.length > 1 && (
                    <div className="flex items-center gap-2">
                      <span className="text-blue-400">⬇</span>
                      <span>ירידה בדקות 16-18: <b className="text-blue-300">{descentDelta.toFixed(1)} מ'</b> — דיליי עייפות טבעי</span>
                    </div>
                  )}
                  <div className="flex items-center gap-2">
                    <span className="text-violet-400">👟</span>
                    <span>נעליים: EVO SL · סך העלייה הכולל: {fmtAscent(selected.total_ascent)} מ'</span>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="bg-zinc-900/80 rounded-2xl p-20 text-center border border-zinc-800">
              <Activity className="w-12 h-12 text-zinc-700 mx-auto mb-4" />
              <p className="text-zinc-500">בחר ריצה או העלה קובץ GPX חדש</p>
            </div>
          )}
        </section>
      </main>

      {/* Mobile FAB */}
      {!sidebarOpen && (
        <button
          onClick={() => setSidebarOpen(true)}
          className="fixed bottom-5 right-5 z-30 md:hidden w-12 h-12 rounded-full bg-violet-600 text-white shadow-lg grid place-items-center"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      )}
    </div>
  )
}