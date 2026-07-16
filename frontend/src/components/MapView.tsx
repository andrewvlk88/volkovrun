import { useEffect, useMemo, useRef } from 'react'
import { MapContainer, TileLayer, Polyline, useMap } from 'react-leaflet'
import type { Map as LeafletMap } from 'leaflet'
import type { MapPosition } from '../types'

// ── Demo fallback: route around Rosh HaAyin (32.084, 34.975) ─────────
const DEMO_POSITIONS: MapPosition[] = [
  { lat: 32.08525, lon: 34.97647 },
  { lat: 32.08427, lon: 34.97597 },
  { lat: 32.08387, lon: 34.97602 },
  { lat: 32.08413, lon: 34.97741 },
  { lat: 32.08463, lon: 34.97641 },
  { lat: 32.08525, lon: 34.97647 },
]

// ── Helper: fit map bounds to polyline ────────────────────────────────
function FitBounds({ positions }: { positions: [number, number][] }) {
  const map = useMap()
  useEffect(() => {
    if (positions.length > 1) {
      map.fitBounds(positions, { padding: [40, 40] })
    }
  }, [map, positions])
  return null
}

interface MapViewProps {
  positions?: MapPosition[]
  /** optional extra stats for pills */
  avgSpeed?: number
  maxEle?: number
  avgHr?: number
}

export default function MapView({ positions, avgSpeed, maxEle, avgHr }: MapViewProps) {
  const mapRef = useRef<LeafletMap | null>(null)

  const pts: MapPosition[] = useMemo(() => {
    if (positions && positions.length > 1) return positions
    return DEMO_POSITIONS
  }, [positions])

  const latlngs: [number, number][] = useMemo(
    () => pts.map((p) => [p.lat, p.lon]),
    [pts],
  )

  const hasRealData = (positions?.length ?? 0) > 1

  return (
    <div className="card p-2">
      <div className="h-[380px] rounded-[16px] overflow-hidden">
        <MapContainer
          center={latlngs[0]}
          zoom={15}
          style={{ height: '100%', width: '100%' }}
          ref={(m: LeafletMap | null) => {
            mapRef.current = m
          }}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; OpenStreetMap'
          />
          <Polyline
            positions={latlngs}
            pathOptions={{ color: '#ef4444', weight: 5, opacity: 0.9 }}
          />
          <FitBounds positions={latlngs} />
        </MapContainer>
      </div>
      <div className="p-3 flex gap-2 flex-wrap">
        <span className="pill bg-action text-white">
          מהירות {avgSpeed ? `${avgSpeed.toFixed(1)} קמ"ש` : '—'}
        </span>
        <span className="pill bg-zinc-100">
          גובה {maxEle ? `${maxEle.toFixed(0)}מ` : '—'}
        </span>
        <span className="pill bg-zinc-100">
          דופק {avgHr ? `${avgHr.toFixed(0)}` : '—'}
        </span>
        {!hasRealData && (
          <span className="pill bg-amber text-white mr-auto">מסלול דמו — ראש העין</span>
        )}
        {hasRealData && (
          <span className="pill bg-positive text-white mr-auto">
            {pts.length} נקודות GPS
          </span>
        )}
      </div>
    </div>
  )
}