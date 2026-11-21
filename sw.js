const CACHE="portugues-v3";
const CORE=["./","index.html","manifest.webmanifest","icon-180.png","icon-192.png","icon-512.png"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting()))});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener("fetch",e=>{
  const req=e.request;if(req.method!=="GET")return;
  const url=new URL(req.url);
  if(url.origin===location.origin){
    // pages: network first so updates arrive, cache when offline
    if(req.mode==="navigate"){
      e.respondWith(fetch(req).then(res=>{const c=res.clone();caches.open(CACHE).then(x=>x.put("index.html",c));return res}).catch(()=>caches.match("index.html")));
      return;
    }
    e.respondWith(caches.match(req).then(hit=>hit||fetch(req).then(res=>{const c=res.clone();caches.open(CACHE).then(x=>x.put(req,c));return res})));
    return;
  }
  if(/fonts\.(googleapis|gstatic)\.com$/.test(url.hostname)){
    e.respondWith(caches.open(CACHE).then(c=>c.match(req).then(hit=>{
      const net=fetch(req).then(res=>{c.put(req,res.clone());return res}).catch(()=>hit);
      return hit||net;
    })));
  }
});
