import type { LapData } from '../types'

interface LapsTableProps {
  laps: LapData[]
}

// Determine row styling: fast laps = green tint, cooldown = gray tint.
function lapRowClass(lap: LapData): string {
  // pace is like "5:33" — parse to seconds for comparison
  const paceParts = String(lap.pace).split(':')
  const paceSec = paceParts.length === 2
    ? parseInt(paceParts[0]) * 60 + parseInt(paceParts[1])
    : 999

  if (paceSec > 0 && paceSec < 360) {
    // sub-6:00 pace = fast interval rep
    return 'bg-positive/10'
  }
  if (paceSec >= 600) {
    // 10:00+ pace = cooldown / recovery
    return 'bg-zinc-50'
  }
  return ''
}

export default function LapsTable({ laps }: LapsTableProps) {
  if (!laps || laps.length === 0) {
    return (
      <div className="card p-5">
        <div className="font-black text-[14px] mb-3">הקפות</div>
        <div className="font-mono text-[12px] text-zinc-500">
          אין נתוני הקפות עבור ריצה זו
        </div>
      </div>
    )
  }

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="font-black text-[14px]">הקפות</div>
        <span className="pill bg-zinc-100">{laps.length} הקפות</span>
      </div>

      {/* Header row */}
      <div className="hidden sm:grid grid-cols-[28px_1fr_1fr_1fr_1fr_1fr] gap-2 text-[10px] font-black tracking-widest text-zinc-400 uppercase px-2 pb-2 border-b border-zinc-100">
        <div>#</div>
        <div>זמן</div>
        <div>מרחק</div>
        <div>קצב</div>
        <div>דופק</div>
        <div>עומס</div>
      </div>

      {/* Lap rows */}
      <div className="space-y-1 mt-2">
        {laps.map((lap) => (
          <div
            key={lap.lap}
            className={`grid grid-cols-[28px_1fr_1fr_1fr_1fr_1fr] gap-2 items-center px-2 py-2 rounded-[10px] font-mono text-[12px] ${lapRowClass(lap)}`}
          >
            <div className="font-black text-zinc-500">{lap.lap}</div>
            <div>{lap.time}</div>
            <div>{lap.distance}</div>
            <div className={lapRowClass(lap).includes('positive') ? 'text-positive font-bold' : ''}>
              {lap.pace}
            </div>
            <div>
              <span className="text-action font-bold">{lap.hr}</span>
              <span className="text-zinc-400">/{lap.max_hr}</span>
            </div>
            <div className="text-amber font-bold">{lap.power}W</div>
          </div>
        ))}
      </div>

      {/* Extra metrics footer */}
      {laps[0] && (
        <div className="mt-4 pt-3 border-t border-zinc-100 grid grid-cols-3 gap-2 text-[11px]">
          <div>
            <div className="font-black text-zinc-400 tracking-widest text-[9px]">CADENCE</div>
            <div className="font-mono font-bold">{laps[0].cadence} spm</div>
          </div>
          <div>
            <div className="font-black text-zinc-400 tracking-widest text-[9px]">GCT</div>
            <div className="font-mono font-bold">{laps[0].gct} ms</div>
          </div>
          <div>
            <div className="font-black text-zinc-400 tracking-widest text-[9px]">STRIDE</div>
            <div className="font-mono font-bold">{laps[0].stride} מ</div>
          </div>
        </div>
      )}
    </div>
  )
}