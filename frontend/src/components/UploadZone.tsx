
import React, {useCallback} from 'react'
export default function UploadZone({onUpload}:{onUpload:(f:File)=>void}){
  const onDrop=useCallback((e:React.DragEvent)=>{e.preventDefault(); const f=e.dataTransfer.files[0]; if(f) onUpload(f)},[onUpload])
  return (
    <div onDragOver={e=>e.preventDefault()} onDrop={onDrop} className="border-2 border-dashed border-gray-300 rounded-2xl p-10 text-center bg-white hover:border-black transition">
      <p className="text-lg font-bold">גרור קובץ Garmin לכאן או לחץ לבחירה</p>
      <p className="text-sm text-gray-500 mt-2">תומך ב .GPX, .KML, .CSV, .TCX</p>
      <input type="file" accept=".gpx,.kml,.csv,.txt,.tcx" className="hidden" id="filein" onChange={e=>{if(e.target.files?.[0]) onUpload(e.target.files[0])}}/>
      <label htmlFor="filein" className="mt-4 inline-block bg-black text-white px-6 py-2 rounded-full cursor-pointer">בחר קובץ</label>
    </div>
  )
}
