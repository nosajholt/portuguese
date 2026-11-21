const CACHE="portugues-v4";
const CORE=["./","index.html","manifest.webmanifest","icon-180.png","icon-192.png","icon-512.png"];
async function precache(){
  const c=await caches.open(CACHE);
  await c.addAll(CORE);
  // recorded voice clips, if they exist yet
  try{
    const res=await fetch("audio/index.json",{cache:"no-cache"});
    if(res.ok){
      await c.put("audio/index.json",res.clone());
      const d=await res.json();
      const files=[...new Set(Object.values(d.clips||{}).filter(Boolean))];
      for(let i=0;i<files.length;i+=20) await c.addAll(files.slice(i,i+20)).catch(()=>{});
    }
  }catch(e){}
}
self.addEventListener("install",e=>{e.waitUntil(precache().then(()=>self.skipWaiting()))});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener("fetch",e=>{
  const req=e.request;if(req.method!=="GET")return;
  const url=new URL(req.url);
  if(url.origin===location.origin){
    if(req.mode==="navigate"||url.pathname.endsWith("/audio/index.json")){
      const key=req.mode==="navigate"?"index.html":"audio/index.json";
      e.respondWith(fetch(req).then(res=>{if(res.ok){const c=res.clone();caches.open(CACHE).then(x=>x.put(key,c))}return res}).catch(()=>caches.match(key)));
      return;
    }
    e.respondWith(caches.match(req,{ignoreSearch:true}).then(hit=>hit||fetch(req).then(res=>{if(res.ok){const c=res.clone();caches.open(CACHE).then(x=>x.put(req,c))}return res})));
    return;
  }
  if(/fonts\.(googleapis|gstatic)\.com$/.test(url.hostname)){
    e.respondWith(caches.open(CACHE).then(c=>c.match(req).then(hit=>{
      const net=fetch(req).then(res=>{c.put(req,res.clone());return res}).catch(()=>hit);
      return hit||net;
    })));
  }
});
