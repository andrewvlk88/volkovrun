import { ComposedChart, Line, Area, XAxis, YAxis, Tooltip, ReferenceArea, ResponsiveContainer, CartesianGrid } from 'recharts'

export default function TimelineView({data}:{data:any}){
  if(!data) return <div className="card p-12 text-center font-mono">טוען תצוגה מאוחדת...</div>
  const recoveryScore=data.recovery?.recovery_score||68
  const strain=data.recovery?.day_strain||11.2
  const rhr=data.recovery?.resting_heart_rate||54
  const hrv=data.recovery?.hrv_rmssd_ms||72

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-12 gap-3">
        <div className="col-span-8 card p-5 flex items-center justify-between">
          <div>
            <div className="text-[11px] font-black tracking-widest text-zinc-500">WHOOP RECOVERY</div>
            <div className="flex items-baseline gap-2">
              <span className="font-black text-[36px] leading-none">{recoveryScore}%</span>
              <span className={`pill ${recoveryScore>66?'bg-positive text-white':'bg-amber text-white'}`}>צהוב</span>
            </div>
          </div>
          <div className="flex gap-2">
            <div className="text-center"><div className="text-[10px] font-black text-zinc-500">RHR</div><div className="font-mono font-bold text-[18px]">{rhr}</div></div>
            <div className="w-px bg-zinc-100 mx-2"/>
            <div className="text-center"><div className="text-[10px] font-black text-zinc-500">HRV</div><div className="font-mono font-bold text-[18px]">{hrv}ms</div></div>
          </div>
        </div>
        <div className="col-span-4 card p-5 bg-zinc-900 text-white">
          <div className="text-[11px] font-black tracking-widest opacity-60">GARMIN 6x2</div>
          <div className="font-black text-[24px] leading-none mt-1">4.08 KM 37:13</div>
          <div className="font-mono text-[12px] mt-1 opacity-80">4:57 פיניש 373W • 162 MAX</div>
        </div>
      </div>

      <div className="card p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="font-black text-[20px]">התאמת שעות - דופק כפול Whoop + Garmin</h2>
          <div className="flex gap-2">
            <span className="pill bg-zinc-100 border">Whoop אפור</span>
            <span className="pill bg-action text-white">Garmin אדום</span>
          </div>
        </div>
        <div className="h-[420px] w-full" dir="ltr">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={[...(data.whoop_24h||[]), ...(data.timeline||[])]} >
              <CartesianGrid stroke="#f4f4f5" vertical={false}/>
              <XAxis dataKey="t_idt" tick={{fontFamily:'JetBrains Mono', fontSize:11}} interval={80}/>
              <YAxis domain={[40,175]} tick={{fontFamily:'JetBrains Mono', fontSize:11}}/>
              <Tooltip contentStyle={{borderRadius:16, fontFamily:'Heebo', border:'1px solid #e4e4e7'}} 
                formatter={(v:any,k:any)=>[v, k==='garmin_hr'?'Garmin HR':k==='whoop_hr'?'Whoop HR':k]}
                labelFormatter={(l)=>`שעה ${l} IDT`}/>
              <ReferenceArea x1="23:10" x2="06:45" fill="#3b82f6" fillOpacity={0.06} label={{value:'שינה 7h12m 82%', position:'insideTopLeft', fontSize:10}}/>
              <ReferenceArea x1="07:41:00" x2="08:18:00" fill="#f59e0b" fillOpacity={0.10} label={{value:'ריצה 6x2', position:'insideTop', fontSize:10}}/>
              <Area dataKey="hr" type="monotone" fill="#f4f4f5" stroke="#a1a1aa" strokeWidth={1.5} dot={false} name="Whoop 24h"/>
              <Area dataKey="whoop_hr" type="monotone" fill="transparent" stroke="#a1a1aa" strokeWidth={1.5} dot={false}/>
              <Line dataKey="garmin_hr" type="monotone" stroke="#ef4444" strokeWidth={3} dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <div className="grid grid-cols-4 gap-3 mt-6">
          <div className="pill bg-zinc-50 border text-center">שינה <b className="font-mono">7h12m 82%</b></div>
          <div className="pill bg-zinc-50 border text-center">Strain <b className="font-mono">{strain}</b></div>
          <div className="pill bg-zinc-50 border text-center">דלתא HR <b className="font-mono">-5 עד +6</b></div>
          <div className="pill bg-positive text-white text-center">EVO SL • 28מ עלייה</div>
        </div>
      </div>
    </div>
  )
}
