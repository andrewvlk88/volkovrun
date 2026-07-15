import { haversine } from './haversine'
export function movingAverage(arr:number[], w=15){
  // edge-padded convolution - מונעת רמפות מלאכותיות
  const padded=[...Array(Math.floor(w/2)).fill(arr[0]), ...arr, ...Array(Math.floor(w/2)).fill(arr[arr.length-1])]
  const res=[]
  for(let i=0;i<arr.length;i++){
    const slice=padded.slice(i,i+w)
    res.push(slice.reduce((a,b)=>a+b,0)/w)
  }
  return res
}
