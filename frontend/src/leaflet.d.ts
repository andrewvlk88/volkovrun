// Minimal leaflet type declarations for react-leaflet compatibility.
// @types/leaflet is not installed; this provides just enough surface area.

export type LatLngExpression = [number, number] | { lat: number; lng: number }
export type LatLngTuple = [number, number]
export type LatLngBoundsExpression = LatLngExpression[]

export interface MapOptions {
  center?: LatLngExpression
  zoom?: number
  minZoom?: number
  maxZoom?: number
  zoomControl?: boolean
  attributionControl?: boolean
  scrollWheelZoom?: boolean
  [key: string]: unknown
}

export interface FitBoundsOptions {
  padding?: [number, number] | number
  paddingTopLeft?: [number, number]
  paddingBottomRight?: [number, number]
  maxZoom?: number
  [key: string]: unknown
}

export interface PolylineOptions {
  color?: string
  weight?: number
  opacity?: number
  lineCap?: string
  lineJoin?: string
  dashArray?: string
  [key: string]: unknown
}

export interface PathOptions extends PolylineOptions {
  fillColor?: string
  fillOpacity?: number
  fillRule?: string
  [key: string]: unknown
}

export interface TileLayerOptions {
  url: string
  attribution?: string
  minZoom?: number
  maxZoom?: number
  maxNativeZoom?: number
  [key: string]: unknown
}

export class Map {
  fitBounds(bounds: LatLngBoundsExpression, options?: FitBoundsOptions): void
  setView(center: LatLngExpression, zoom: number): void
  getBounds(): LatLngBounds
  [key: string]: unknown
}

export class LatLngBounds {
  constructor(southWest: LatLngExpression, northEast: LatLngExpression)
  extend(latlng: LatLngExpression): this
  [key: string]: unknown
}

export class Polyline {
  setLatLngs(latlngs: LatLngExpression[]): this
  getLatLngs(): LatLngExpression[]
  [key: string]: unknown
}

export class TileLayer {
  [key: string]: unknown
}

export class Marker {
  [key: string]: unknown
}

export class Icon {
  constructor(options: Record<string, unknown>)
  [key: string]: unknown
}