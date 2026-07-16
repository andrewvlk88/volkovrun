import { useCallback, useEffect, useMemo, useState } from 'react'
import TimelineView from './components/TimelineView'
import MapView from './components/MapView'
import UploadZone from './components/UploadZone'
import LapsTable from './components/LapsTable'
import type {
  RunSummary,
  RunDetail,
  UnifiedTimeline,
  LapData,
  MapPosition,
} from './types'

// ── Helpers ──────────────────────────────────────────────────────────

function formatDuration(sec: number): string {
  if (!sec || sec <= 0) return '—'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function formatRunDate(iso: string): string {
  if (!iso) return 'ללא תאריך'
  try {
    return new Date(iso).toLocaleString('he-IL', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Asia/Jerusalem',
    })
  } catch {
    return iso
  }
}

// Generate synthetic lap data from run detail (since the API doesn't
// return structured laps — we split by distance or time).
function deriveLaps(run: RunDetail | null): LapData[] {
  if (!run || !run.points || run.points.length === 0) return []

  const pts = run.points
  const totalDist = run.distance || 0
  const numLaps = Math.min(6, Math.max(2, Math.ceil(totalDist)))
  const lapDist = totalDist / numLaps

  const laps: LapData[] = []
  let currentLap = 1
  let lapStartIdx = 0
  let targetDist = lapDist

  for (let i = 0; i < pts.length; i++) {
    const d = pts[i].dist || 0
    if (d >= targetDist || (i === pts.length - 1 && currentLap <= numLaps)) {
      const lapPts = pts.slice(lapStartIdx, i + 1)
      const lapHrs = lapPts.map((p) => p.hr).filter((h) => h > 0)
      const lapDistVal = d - (pts[lapStartIdx]?.dist || 0)
      const lapTimeSec = (pts[i].t ?? 0) - (pts[lapStartIdx]?.t ?? 0) || lapPts.length
      const paceStr = pts[i].pace ? String(pts[i].pace) : '—'
      const ascent = lapPts.reduce((sum, p, idx) => {
        if (idx === 0) return 0
        const diff = (p.ele_smooth || 0) - (lapPts[idx - 1].ele_smooth || 0)
        return sum + (diff > 0 ? diff : 0)
      }, 0)

      laps.push({
        lap: currentLap,
        time: formatDuration(lapTimeSec),
        distance: `${lapDistVal.toFixed(2)} ק"מ`,
        pace: paceStr,
        hr: lapHrs.length ? Math.round(lapHrs.reduce((a, b) => a + b, 0) / lapHrs.length) : 0,
        max_hr: lapHrs.length ? Math.max(...lapHrs) : 0,
        power: 0,
        ascent: Math.round(ascent),
        cadence: 0,
        gct: 0,
        stride: 0,
      })

      currentLap++
      lapStartIdx = i + 1
      targetDist += lapDist
      if (currentLap > numLaps) break
    }
  }

  return laps
}

// ── KPI Card ─────────────────────────────────────────────────────────

interface KPICardProps {
  label: string
  value: string
  unit?: string
  color?: 'action' | 'positive' | 'amber' | 'info' | 'zinc'
}

function KPICard({ label, value, unit, color = 'zinc' }: KPICardProps) {
  const colorMap: Record<string, string> = {
    action: 'text-action',
    positive: 'text-positive',
    amber: 'text-amber',
    info: 'text-info',
    zinc: 'text-zinc-900',
  }
  return (
    <div className="card p-5">
      <div className="text-[10px] font-black tracking-widest text-zinc-400 uppercase">
        {label}
      </div>
      <div className="flex items-baseline gap-1 mt-2">
        <span className={`font-black text-[28px] leading-none font-mono ${colorMap[color]}`}>
          {value}
        </span>
        {unit && <span className="text-[14px] text-zinc-400 font-bold">{unit}</span>}
      </div>
    </div>
  )
}

// ── Main App ─────────────────────────────────────────────────────────

export default function App() {
  const [timeline, setTimeline] = useState<UnifiedTimeline | null>(null)
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null)
  const [selectedRun, setSelectedRun] = useState<RunDetail | null>(null)
  const [loadingRun, setLoadingRun] = useState(false)

  // Load timeline + runs list on mount
  useEffect(() => {
    fetch('/api/timeline?date=2026-07-15')
      .then((r) => r.json())
      .then((d: UnifiedTimeline) => setTimeline(d))
      .catch(() => setTimeline(null))

    fetch('/api/runs')
      .then((r) => r.json())
      .then((d: RunSummary[]) => {
        setRuns(d)
        // Auto-select the first run
        if (d.length > 0 && d[0].id) {
          setSelectedRunId(d[0].id)
        }
      })
      .catch(() => setRuns([]))
  }, [])

  // Load selected run detail
  const loadRun = useCallback((runId: number) => {
    setLoadingRun(true)
    fetch(`/api/runs/${runId}`)
      .then((r) => r.json())
      .then((d: RunDetail) => {
        setSelectedRun(d)
        setLoadingRun(false)
      })
      .catch(() => {
        setSelectedRun(null)
        setLoadingRun(false)
      })
  }, [])

  useEffect(() => {
    if (selectedRunId !== null) {
      loadRun(selectedRunId)
    }
  }, [selectedRunId, loadRun])

  // Derive map positions from selected run
  const mapPositions: MapPosition[] = useMemo(() => {
    if (selectedRun?.points?.length) {
      return selectedRun.points.map((p) => ({ lat: p.lat, lon: p.lon }))
    }
    return []
  }, [selectedRun])

  // Derive laps from selected run
  const laps = useMemo(() => deriveLaps(selectedRun), [selectedRun])

  // KPI values from selected run (or timeline)
  const kpiDistance = selectedRun?.distance ?? 0
  const kpiDuration = selectedRun?.duration ?? 0
  const kpiAvgHr = selectedRun?.avg_hr ?? 0
  const kpiAscent = selectedRun?.total_ascent ?? 0

  // Map stats
  const mapAvgSpeed = useMemo(() => {
    if (!selectedRun?.points?.length) return undefined
    const speeds = selectedRun.points.map((p) => p.speed).filter((s) => s > 0)
    return speeds.length ? speeds.reduce((a, b) => a + b, 0) / speeds.length : undefined
  }, [selectedRun])

  const mapMaxEle = useMemo(() => {
    if (!selectedRun?.points?.length) return undefined
    return Math.max(...selectedRun.points.map((p) => p.ele_smooth || 0))
  }, [selectedRun])

  return (
    <div className="min-h-screen bg-paper">
      {/* ── Header ───────────────────────────────────────────── */}
      <header className="sticky top-0 z-20 bg-white/80 backdrop-blur border-b border-zinc-100">
        <div className="max-w-[1280px] mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-baseline gap-3">
            <h1 className="font-black text-[22px] tracking-tighter">VOLKOV RUN LAB</h1>
            <span className="pill bg-zinc-900 text-white">WHOOP + GARMIN UNIFIED</span>
          </div>
          <div className="flex gap-2">
            <span className="pill bg-white border">EVO SL</span>
            <span className="pill bg-action text-white">{runs.length} ריצות</span>
          </div>
        </div>
      </header>

      <main className="max-w-[1280px] mx-auto px-6 py-8 space-y-6">
        {/* ── Run selector ─────────────────────────────────────── */}
        {runs.length > 0 && (
          <div className="flex gap-2 flex-wrap">
            {runs.map((run) => (
              <button
                key={run.id}
                onClick={() => setSelectedRunId(run.id)}
                className={`pill transition ${
                  selectedRunId === run.id
                    ? 'bg-action text-white'
                    : 'bg-white border hover:bg-zinc-50'
                }`}
              >
                #{run.id} · {run.distance?.toFixed(2) ?? '?'} ק"מ · {formatRunDate(run.start_time)}
              </button>
            ))}
          </div>
        )}

        {/* ── KPI Row ──────────────────────────────────────────── */}
        <div className="grid grid-cols-4 gap-4">
          <KPICard
            label="מרחק"
            value={kpiDistance ? kpiDistance.toFixed(2) : '—'}
            unit='ק"מ'
            color="action"
          />
          <KPICard
            label="זמן"
            value={kpiDuration ? formatDuration(kpiDuration) : '—'}
            color="info"
          />
          <KPICard
            label="דופק ממוצע"
            value={kpiAvgHr ? String(Math.round(kpiAvgHr)) : '—'}
            unit="bpm"
            color="amber"
          />
          <KPICard
            label="עלייה"
            value={kpiAscent ? String(Math.round(kpiAscent)) : '—'}
            unit="מ"
            color="positive"
          />
        </div>

        {/* ── Upload Zone ──────────────────────────────────────── */}
        <UploadZone />

        {/* ── Timeline ─────────────────────────────────────────── */}
        <TimelineView data={timeline} />

        {/* ── Map + Laps grid ──────────────────────────────────── */}
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-8">
            <MapView
              positions={mapPositions}
              avgSpeed={mapAvgSpeed}
              maxEle={mapMaxEle}
              avgHr={kpiAvgHr}
            />
          </div>
          <div className="col-span-4">
            {loadingRun ? (
              <div className="card p-5 text-center font-mono text-zinc-500">
                טוען הקפות…
              </div>
            ) : (
              <LapsTable laps={laps} />
            )}
          </div>
        </div>

        {/* ── Insights ─────────────────────────────────────────── */}
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-4">
            <span className="pill bg-info text-white">INSIGHTS</span>
            <h2 className="font-black text-[18px] tracking-tighter">תובנות אימון</h2>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <div className="text-[10px] font-black tracking-widest text-zinc-400 uppercase">
                התאמת דופק
              </div>
              <div className="font-mono text-[13px] mt-1">
                {timeline?.timeline?.length
                  ? `דלתא ${Math.min(...timeline.timeline.map((t) => t.diff ?? 0))} עד ${Math.max(...timeline.timeline.map((t) => t.diff ?? 0))} bpm`
                  : '—'}
              </div>
            </div>
            <div>
              <div className="text-[10px] font-black tracking-widest text-zinc-400 uppercase">
                RHR vs דופק ריצה
              </div>
              <div className="font-mono text-[13px] mt-1">
                {timeline?.recovery && selectedRun
                  ? `RHR ${timeline.recovery.resting_heart_rate} → דופק ממוצע ${Math.round(kpiAvgHr)} (+${Math.round(kpiAvgHr - timeline.recovery.resting_heart_rate)})`
                  : '—'}
              </div>
            </div>
            <div>
              <div className="text-[10px] font-black tracking-widest text-zinc-400 uppercase">
                עומס כולל
              </div>
              <div className="font-mono text-[13px] mt-1">
                {timeline?.recovery
                  ? `Strain ${timeline.recovery.day_strain} · ${kpiDistance.toFixed(2)} ק"מ · ${formatDuration(kpiDuration)}`
                  : '—'}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}