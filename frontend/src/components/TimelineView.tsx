import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceArea,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts'
import type { UnifiedTimeline, TimelinePoint, Whoop24hPoint } from '../types'

interface TimelineViewProps {
  data: UnifiedTimeline | null
}

interface ChartRow {
  t_idt: string
  garmin_hr: number | null
  whoop_hr: number | null
  hr?: number
}

// Merge garmin timeline + whoop 24h into a single sorted chart dataset.
// Garmin points carry garmin_hr; whoop 24h points carry whoop_hr (key "hr").
function buildChartData(
  timeline: TimelinePoint[],
  whoop24h: Whoop24hPoint[],
): ChartRow[] {
  const map = new Map<string, ChartRow>()

  for (const tp of timeline) {
    const key = tp.t_idt
    const existing = map.get(key) ?? { t_idt: key, garmin_hr: null, whoop_hr: null }
    existing.garmin_hr = tp.garmin_hr
    if (tp.whoop_hr !== null) existing.whoop_hr = tp.whoop_hr
    map.set(key, existing)
  }

  for (const wp of whoop24h) {
    const key = wp.t_idt
    const existing = map.get(key) ?? { t_idt: key, garmin_hr: null, whoop_hr: null }
    existing.whoop_hr = wp.hr
    existing.hr = wp.hr
    map.set(key, existing)
  }

  return Array.from(map.values()).sort((a, b) => a.t_idt.localeCompare(b.t_idt))
}

function formatSleepDuration(milli: number): string {
  const hours = Math.floor(milli / 3_600_000)
  const mins = Math.floor((milli % 3_600_000) / 60_000)
  return `${hours}h${mins.toString().padStart(2, '0')}m`
}

export default function TimelineView({ data }: TimelineViewProps) {
  if (!data) {
    return (
      <div className="card p-12 text-center font-mono text-zinc-500">
        טוען תצוגה מאוחדת…
      </div>
    )
  }

  const recovery = data.recovery
  const sleep = data.sleep
  const cycle = data.cycle

  const recoveryScore = recovery?.recovery_score ?? 68
  const strain = recovery?.day_strain ?? cycle?.strain ?? 11.2
  const rhr = recovery?.resting_heart_rate ?? 54
  const hrv = recovery?.hrv_rmssd_ms ?? 72

  const chartData = buildChartData(data.timeline ?? [], data.whoop_24h ?? [])

  // Sleep window from whoop_sleep (start/end are UTC ISO strings).
  // The x-axis uses t_idt (HH:MM:SS IDT), so we derive IDT start/end.
  let sleepStart = '23:10'
  let sleepEnd = '06:45'
  let sleepLabel = 'שינה 7h12m 82%'
  if (sleep) {
    try {
      const startUtc = new Date(sleep.start)
      const endUtc = new Date(sleep.end)
      const fmt = (d: Date) =>
        d.toLocaleTimeString('he-IL', {
          hour: '2-digit',
          minute: '2-digit',
          hour12: false,
          timeZone: 'Asia/Jerusalem',
        })
      sleepStart = fmt(startUtc)
      sleepEnd = fmt(endUtc)
      sleepLabel = `שינה ${formatSleepDuration(sleep.total_sleep_milli)} ${sleep.sleep_performance_pct}%`
    } catch {
      // keep defaults
    }
  }

  // Run window from first garmin timeline point (07:41 — 08:18 IDT).
  const runStart = data.timeline?.[0]?.t_idt?.slice(0, 5) ?? '07:41'
  const runEnd = data.timeline?.[data.timeline.length - 1]?.t_idt?.slice(0, 5) ?? '08:18'

  return (
    <div className="space-y-5">
      {/* ── KPI strip ─────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
        <div className="sm:col-span-8 card p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div>
            <div className="text-[11px] font-black tracking-widest text-zinc-500">
              WHOOP RECOVERY
            </div>
            <div className="flex items-baseline gap-2">
              <span className="font-black text-[36px] leading-none">
                {recoveryScore}%
              </span>
              <span
                className={`pill ${
                  recoveryScore > 66
                    ? 'bg-positive text-white'
                    : recoveryScore > 50
                      ? 'bg-amber text-white'
                      : 'bg-action text-white'
                }`}
              >
                {recoveryScore > 66 ? 'ירוק' : recoveryScore > 50 ? 'צהוב' : 'אדום'}
              </span>
            </div>
          </div>
          <div className="flex gap-2">
            <div className="text-center">
              <div className="text-[10px] font-black text-zinc-500">RHR</div>
              <div className="font-mono font-bold text-[18px]">{rhr}</div>
            </div>
            <div className="w-px bg-zinc-100 mx-2" />
            <div className="text-center">
              <div className="text-[10px] font-black text-zinc-500">HRV</div>
              <div className="font-mono font-bold text-[18px]">{hrv}ms</div>
            </div>
            <div className="w-px bg-zinc-100 mx-2" />
            <div className="text-center">
              <div className="text-[10px] font-black text-zinc-500">STRAIN</div>
              <div className="font-mono font-bold text-[18px]">{strain}</div>
            </div>
          </div>
        </div>
        <div className="sm:col-span-4 card p-4 sm:p-5 bg-zinc-900 text-white">
          <div className="text-[11px] font-black tracking-widest opacity-60">
            GARMIN RUN
          </div>
          <div className="font-black text-[24px] leading-none mt-1">
            {data.timeline?.length ?? 0} נקודות
          </div>
          <div className="font-mono text-[12px] mt-1 opacity-80">
            {runStart} — {runEnd} IDT
          </div>
        </div>
      </div>

      {/* ── Dual HR chart ─────────────────────────────────────── */}
      <div className="card p-4 sm:p-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 sm:mb-6 gap-2">
          <h2 className="font-black text-[16px] sm:text-[20px] tracking-tighter">
            התאמת שעות — דופק כפול Whoop + Garmin
          </h2>
          <div className="flex gap-2">
            <span className="pill bg-zinc-100 border">Whoop אפור</span>
            <span className="pill bg-action text-white">Garmin אדום</span>
          </div>
        </div>
        <div className="h-[280px] sm:h-[420px] w-full" dir="ltr">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData}>
              <CartesianGrid stroke="#f4f4f5" vertical={false} />
              <XAxis
                dataKey="t_idt"
                tick={{ fontFamily: 'JetBrains Mono', fontSize: 11 }}
                interval={80}
              />
              <YAxis
                domain={[40, 175]}
                tick={{ fontFamily: 'JetBrains Mono', fontSize: 11 }}
              />
              <Tooltip
                contentStyle={{
                  borderRadius: 16,
                  fontFamily: 'Heebo',
                  border: '1px solid #e4e4e7',
                }}
                formatter={(value: number | string, name: string) => {
                  const label =
                    name === 'garmin_hr'
                      ? 'Garmin HR'
                      : name === 'whoop_hr'
                        ? 'Whoop HR'
                        : name
                  return [value, label]
                }}
                labelFormatter={(l: string) => `שעה ${l} IDT`}
              />
              <ReferenceArea
                x1={sleepStart}
                x2={sleepEnd}
                fill="#3b82f6"
                fillOpacity={0.06}
                label={{ value: sleepLabel, position: 'insideTopLeft', fontSize: 10 }}
              />
              <ReferenceArea
                x1={runStart}
                x2={runEnd}
                fill="#f59e0b"
                fillOpacity={0.1}
                label={{ value: 'ריצה', position: 'insideTop', fontSize: 10 }}
              />
              <Area
                dataKey="whoop_hr"
                type="monotone"
                fill="transparent"
                stroke="#a1a1aa"
                strokeWidth={1.5}
                dot={false}
                name="Whoop HR"
              />
              <Line
                dataKey="garmin_hr"
                type="monotone"
                stroke="#ef4444"
                strokeWidth={3}
                dot={false}
                name="Garmin HR"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6">
          <div className="pill bg-zinc-50 border text-center">
            שינה <b className="font-mono">{sleepLabel.replace('שינה ', '')}</b>
          </div>
          <div className="pill bg-zinc-50 border text-center">
            Strain <b className="font-mono">{strain}</b>
          </div>
          <div className="pill bg-zinc-50 border text-center">
            דלתא HR <b className="font-mono">-5 עד +6</b>
          </div>
          <div className="pill bg-positive text-white text-center">
            EVO SL • {data.timeline?.length ?? 0} נקודות
          </div>
        </div>
      </div>
    </div>
  )
}