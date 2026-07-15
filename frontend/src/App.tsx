import { useEffect, useState } from 'react'
import MapView from './components/MapView'
import TimelineView from './components/TimelineView'
import UploadZone from './components/UploadZone'

export default function App() {
  const [timeline, setTimeline] = useState<any>(null)
  const [runs, setRuns] = useState<any[]>([])

  useEffect(() => {
    fetch('/api/runs').then(r => r.json()).then(setRuns)
    fetch('/api/timeline?date=2026-07-14').then(r => r.json()).then(setTimeline)
  }, [])

  return (
    <div className="min-h-screen bg-paper">
      <header className="sticky top-0 z-10 bg-white/80 backdrop-blur border-b border-zinc-100">
        <div className="max-w-[1280px] mx-auto px-6 py-4 flex justify-between items-center">
          <h1 className="font-black text-[20px] tracking-tight">VOLKOV RUN LAB</h1>
          <div className="flex gap-2">
            <span className="pill bg-action text-white">EVO SL</span>
            <span className="pill bg-zinc-900 text-white">{runs.length} ריצות</span>
          </div>
        </div>
      </header>

      <main className="max-w-[1280px] mx-auto px-6 py-8 space-y-6">
        <UploadZone />
        {timeline && <TimelineView data={timeline} />}
        <MapView points={[]} colorBy="ele" />
      </main>
    </div>
  )
}