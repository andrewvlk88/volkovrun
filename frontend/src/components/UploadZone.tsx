import { useCallback, useRef, useState } from 'react'
import type { UploadResult } from '../types'

type UploadState = 'idle' | 'uploading' | 'success' | 'error'

function formatDuration(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

export default function UploadZone() {
  const [state, setState] = useState<UploadState>('idle')
  const [result, setResult] = useState<UploadResult | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [fileName, setFileName] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const uploadFile = useCallback(async (file: File) => {
    setFileName(file.name)
    setState('uploading')
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      })
      const data: UploadResult = await res.json()
      if (data.error) {
        setState('error')
        setResult(data)
      } else {
        setState('success')
        setResult(data)
      }
    } catch (err) {
      setState('error')
      setResult({ error: String(err) })
    }
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault()
      setDragOver(false)
      const file = e.dataTransfer.files[0]
      if (file) uploadFile(file)
    },
    [uploadFile],
  )

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) uploadFile(file)
    },
    [uploadFile],
  )

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(e) => {
        e.preventDefault()
        setDragOver(true)
      }}
      onDragLeave={() => setDragOver(false)}
      className={`card p-6 border-2 border-dashed transition ${
        dragOver
          ? 'border-action bg-action/5'
          : 'border-zinc-200 bg-zinc-50/50'
      }`}
    >
      {state === 'idle' && (
        <div className="text-center">
          <div className="font-black text-[18px]">גרור GPX / KML / TCX / CSV לכאן</div>
          <div className="font-mono text-[11px] text-zinc-500 mt-1">
            סנכרון אוטומטי Garmin כל 30 דקות • Whoop כל 15 דקות • התאמת שעות IDT
          </div>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="btn mt-4"
          >
            בחר קובץ
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".gpx,.kml,.tcx,.csv,.txt"
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>
      )}

      {state === 'uploading' && (
        <div className="text-center">
          <div className="font-black text-[18px]">מעלה {fileName}…</div>
          <div className="font-mono text-[11px] text-zinc-500 mt-1">
            מפענח נתונים…
          </div>
        </div>
      )}

      {state === 'success' && result && (
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="pill bg-positive text-white">הועלה</span>
              <span className="font-mono text-[12px] text-zinc-500">{fileName}</span>
            </div>
            <div className="mt-3 flex gap-6">
              <div>
                <div className="text-[10px] font-black tracking-widest text-zinc-500">מרחק</div>
                <div className="font-mono font-bold text-[20px]">
                  {result.distance_km?.toFixed(2) ?? '—'} ק"מ
                </div>
              </div>
              <div>
                <div className="text-[10px] font-black tracking-widest text-zinc-500">זמן</div>
                <div className="font-mono font-bold text-[20px]">
                  {result.duration_str ?? (result.duration_sec ? formatDuration(result.duration_sec) : '—')}
                </div>
              </div>
              <div>
                <div className="text-[10px] font-black tracking-widest text-zinc-500">דופק ממוצע</div>
                <div className="font-mono font-bold text-[20px]">
                  {result.avg_hr ?? '—'}
                </div>
              </div>
              <div>
                <div className="text-[10px] font-black tracking-widest text-zinc-500">דופק מקס</div>
                <div className="font-mono font-bold text-[20px]">
                  {result.max_hr ?? '—'}
                </div>
              </div>
              <div>
                <div className="text-[10px] font-black tracking-widest text-zinc-500">עלייה</div>
                <div className="font-mono font-bold text-[20px]">
                  {result.total_ascent ?? '—'}מ
                </div>
              </div>
            </div>
          </div>
          <button
            onClick={() => {
              setState('idle')
              setResult(null)
              setFileName('')
            }}
            className="pill bg-zinc-100 hover:bg-zinc-200 transition"
          >
            העלאה נוספת
          </button>
        </div>
      )}

      {state === 'error' && (
        <div className="text-center">
          <span className="pill bg-action text-white">שגיאה</span>
          <div className="font-mono text-[12px] text-action mt-2">
            {result?.error ?? 'שגיאה לא ידועה'}
          </div>
          <button
            onClick={() => {
              setState('idle')
              setResult(null)
              setFileName('')
            }}
            className="pill bg-zinc-100 hover:bg-zinc-200 transition mt-3"
          >
            נסה שוב
          </button>
        </div>
      )}
    </div>
  )
}