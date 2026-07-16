// ── API response types ──────────────────────────────────────────────

export interface RunSummary {
  id: number
  start_time: string
  distance: number
  duration: number
  avg_pace: string
  avg_hr: number
  max_hr: number
  total_ascent: number | null
  total_descent: number | null
  shoes: string
  raw_stats: string
  created_at: string
}

export interface TrackPoint {
  id?: number
  run_id?: number
  t: number | null
  lat: number
  lon: number
  ele: number
  ele_smooth: number
  hr: number
  speed: number
  pace: number | string
  dist: number
}

export interface WhoopRecovery {
  id?: number
  date: string
  recovery_score: number
  resting_heart_rate: number
  hrv_rmssd_ms: number
  spo2_pct: number
  skin_temp_c: number
  day_strain: number
}

export interface WhoopSleep {
  id?: number
  date: string
  start: string
  end: string
  total_sleep_milli: number
  sleep_performance_pct: number
  deep_sleep_milli: number
  rem_sleep_milli: number
  light_sleep_milli: number
}

export interface WhoopCycle {
  id?: number
  start: string
  end: string
  strain: number
  kilojoule: number
  avg_heart_rate: number
  max_heart_rate: number
}

export interface TimelinePoint {
  t_utc: string
  t_idt: string
  garmin_hr: number
  whoop_hr: number | null
  diff: number | null
  ele: number
  speed: number
  pace: number | string
}

export interface Whoop24hPoint {
  t_idt: string
  hr: number
}

export interface UnifiedTimeline {
  recovery: WhoopRecovery | null
  sleep: WhoopSleep | null
  cycle: WhoopCycle | null
  timeline: TimelinePoint[]
  whoop_24h: Whoop24hPoint[]
}

export interface RunDetail extends RunSummary {
  points: TrackPoint[]
  whoop: WhoopRecovery | null
}

export interface UploadResult {
  id?: number
  filename?: string
  error?: string
  distance_km?: number
  duration_sec?: number
  duration_str?: string
  avg_pace?: string
  avg_hr?: number
  max_hr?: number
  total_ascent?: number
  is_continuous?: boolean
  points?: TrackPoint[]
}

// ── Component prop types ────────────────────────────────────────────

export interface MapPosition {
  lat: number
  lon: number
}

export interface LapData {
  lap: number
  time: string
  distance: string
  pace: string
  hr: number
  max_hr: number
  power: number
  ascent: number
  cadence: number
  gct: number
  stride: number
}