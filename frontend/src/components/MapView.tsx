import { useEffect } from 'react'
import { MapContainer, TileLayer, Polyline, Marker } from 'react-leaflet'
import L from 'leaflet'

export default function MapView(){
  const positions: [number, number][] = [[32.08525,34.97647],[32.08427,34.97597],[32.08387,34.97602],[32.08463,34.97641]]
  return (
    <div className="card p-2">
      <div className="h-[380px] rounded-[16px] overflow-hidden">
        <MapContainer center={positions[0]} zoom={15} style={{height:'100%', width:'100%'}}>
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>
          <Polyline positions={positions} pathOptions={{color:'#ef4444', weight:5}}/>
        </MapContainer>
      </div>
      <div className="p-3 flex gap-2">
        <span className="pill bg-action text-white">מהירות</span>
        <span className="pill bg-zinc-100">גובה</span>
        <span className="pill bg-zinc-100">דופק</span>
        <span className="pill bg-amber text-white ml-auto">עלייה 8.4מ ב Run4</span>
      </div>
    </div>
  )
}
