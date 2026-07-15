import { useEffect, useState } from 'react'
import TimelineView from './components/TimelineView'
import MapView from './components/MapView'
import UploadZone from './components/UploadZone'

export default function App(){
  const [timeline,setTimeline]=useState<any>(null)
  const [runs,setRuns]=useState<any[]>([])
  useEffect(()=>{
    fetch('/api/timeline?date=2026-07-14').then(r=>r.json()).then(setTimeline).catch(()=>{})
    fetch('/api/runs').then(r=>r.json()).then(setRuns).catch(()=>{})
  },[])
  return (
    <div className="min-h-screen bg-paper">
      <header className="sticky top-0 z-20 bg-white/80 backdrop-blur border-b border-zinc-100">
        <div className="max-w-[1280px] mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-baseline gap-3">
            <h1 className="font-black text-[22px] tracking-tighter">VOLKOV RUN LAB</h1>
            <span className="pill bg-zinc-900 text-white">WHOOP + GARMIN UNIFIED</span>
          </div>
          <div className="flex gap-2">
            <span className="pill bg-white border">EVO SL</span>
            <span className="pill bg-action text-white">{runs.length||1} ריצות</span>
          </div>
        </div>
      </header>
      <main className="max-w-[1280px] mx-auto px-6 py-8 space-y-6">
        <UploadZone/>
        <TimelineView data={timeline}/>
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-8"><MapView/></div>
          <div className="col-span-4 space-y-4">
            <div className="card p-5">
              <div className="font-black text-[14px] mb-3">אינטרוולים היום - 6x2</div>
              <div className="space-y-2 font-mono text-[12px]">
                <div className="flex justify-between"><span>Run1 6:00</span><span>136/148 HR</span><span>332W</span></div>
                <div className="flex justify-between"><span>Run2 5:38</span><span>125/137</span><span>318W</span></div>
                <div className="flex justify-between"><span>Run3 5:24</span><span>131/148</span><span>304W</span></div>
                <div className="flex justify-between text-amber font-bold"><span>Run4 6:36 עלייה 8.4מ</span><span>136/153</span><span>322W</span></div>
                <div className="flex justify-between"><span>Run5 6:12</span><span>134/142</span><span>298W</span></div>
                <div className="flex justify-between bg-positive/10 p-2 rounded-full"><span>Run6 4:57</span><span>139/161</span><span>373W 4.82</span></div>
              </div>
            </div>
            <div className="card p-5">
              <div className="font-black text-[12px] tracking-widest text-zinc-500">POWER + GCT</div>
              <div className="mt-2 font-mono text-[13px]">GCT 259ms פיניש, שיפור 30ms מ Run1, צעד 1.20מ</div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
