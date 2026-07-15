import { ComposedChart, Line, Area, XAxis, YAxis, Tooltip, ReferenceArea, ResponsiveContainer } from 'recharts'

export default function TimelineView({ data }: { data: any }) {
  if (!data) return null
  return (
    <div className="card p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="font-black text-[22px]">תצוגה מאוחדת Whoop + Garmin</h2>
        <div className="flex gap-2">
          <span className="pill bg-zinc-900 text-white">Recovery {data.recovery?.recovery_score}%</span>
          <span className="pill bg-positive/10 text-positive border border-positive/20">{data.cycle?.strain} Strain</span>
        </div>
      </div>

      <div className="h-[380px] w-full" dir="ltr">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data.timeline}>
            <XAxis dataKey="t_idt" tick={{ fontFamily: 'JetBrains Mono', fontSize: 11 }} />
            <YAxis domain={[40, 180]} tick={{ fontFamily: 'JetBrains Mono' }} />
            <Tooltip
              contentStyle={{ borderRadius: 16, fontFamily: 'Heebo' }}
              formatter={(v: any, k: any) => [v, k]}
              labelFormatter={(l) => `שעה ${l}`}
            />
            <ReferenceArea x1="23:10" x2="06:45" fill="#3b82f6" fillOpacity={0.08} />
            <ReferenceArea x1="07:41:00" x2="08:18:00" fill="#f59e0b" fillOpacity={0.12} />
            <Area dataKey="whoop_hr" type="monotone" fill="#e4e4e7" stroke="#a1a1aa" strokeWidth={1.5} dot={false} />
            <Line dataKey="garmin_hr" type="monotone" stroke="#ef4444" strokeWidth={3} dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-4 gap-3 mt-6">
        <div className="pill bg-zinc-50 border border-zinc-200 text-center">Whoop RHR <span className="font-mono font-bold">{data.recovery?.resting_heart_rate}</span></div>
        <div className="pill bg-zinc-50 border border-zinc-200 text-center">HRV <span className="font-mono font-bold">{data.recovery?.hrv_rmssd_ms}ms</span></div>
        <div className="pill bg-zinc-50 border border-zinc-200 text-center">שינה <span className="font-mono font-bold">{Math.round((data.sleep?.total_sleep_milli || 0) / 3600000 * 10) / 10}h</span></div>
        <div className="pill bg-positive text-white text-center">Garmin {data.runs?.[0]?.distance_km || '--'}km</div>
      </div>
    </div>
  )
}