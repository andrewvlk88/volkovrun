
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet'
import { useEffect } from 'react'
function FitBounds({points}:{points:any[]}){
  const map=useMap()
  useEffect(()=>{ if(points.length){ const b=points.map((p:any)=>[p.lat,p.lon]); // @ts-ignore
    map.fitBounds(b as any) } },[points,map])
  return null
}
export default function MapView({points, colorBy}:{points:any[], colorBy:'speed'|'ele'|'hr'}){
  if(!points.length) return <div className="h-[400px] bg-gray-100 rounded-2xl flex items-center justify-center">אין נתוני מסלול</div>
  const getColor=(p:any)=>{
    if(colorBy==='hr'){ const v=Math.min(170,Math.max(100,p.hr||120)); const t=(v-100)/70; return `rgb(${Math.round(255*t)},${Math.round(200*(1-t))},80)`}
    if(colorBy==='ele'){ const eles=points.map((x:any)=>x.ele_smooth||x.ele); const min=Math.min(...eles), max=Math.max(...eles); const t=(p.ele_smooth-min)/(max-min||1); return `rgb(${Math.round(50+200*t)},${Math.round(150*(1-t))},${Math.round(255*(1-t))})`}
    const v=Math.min(13,Math.max(6,p.speed_kmh||8)); const t=(v-6)/7; return `rgb(${Math.round(255*t)},${Math.round(200*(1-t))},60)`
  }
  return (
    <MapContainer style={{height:500, borderRadius:16}} center={[points[0].lat, points[0].lon]} zoom={14} scrollWheelZoom>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>
      <FitBounds points={points}/>
      {points.slice(1).map((p:any,i:number)=>{const prev=points[i]; const c=getColor(p); return <Polyline key={i} positions={[[prev.lat,prev.lon],[p.lat,p.lon]]} pathOptions={{color:c, weight:5, opacity:0.8}}/>})}
      <Marker position={[points[0].lat, points[0].lon]}><Popup>זינוק</Popup></Marker>
      <Marker position={[points[points.length-1].lat, points[points.length-1].lon]}><Popup>סיום</Popup></Marker>
    </MapContainer>
  )
}
