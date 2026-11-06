from __future__ import annotations
import json, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from .config import load_config, save_config
from .hardware import scan_hardware, recommend, asdict_hw
from .models import scan_models, to_dicts
from .server import start_server, stop_server, status

INDEX = r"""<!doctype html><meta charset=utf-8>
<title>LocalModelPilot</title>
<style>
body{font:14px -apple-system,system-ui,sans-serif;margin:16px;max-width:1100px}
pre{background:#111;color:#eee;padding:10px;overflow:auto;max-height:260px;font-size:12px}
.row{display:flex;gap:12px;flex-wrap:wrap}.card{border:1px solid #ddd;border-radius:8px;padding:12px;flex:1;min-width:280px}
input,select{padding:6px;margin:2px 0;width:100%;box-sizing:border-box} button{padding:6px 10px;margin-right:6px;cursor:pointer}
table{border-collapse:collapse;width:100%;font-size:12px} td,th{border-bottom:1px solid #eee;padding:4px;text-align:left}
small{color:#555}.ok{color:#0a7}.bad{color:#c33}
</style>
<h2>LocalModelPilot <small>(local, reuses existing llama-server)</small></h2>
<div class=row>
 <div class=card><h3>Hardware</h3><div id=hw>loading…</div></div>
 <div class=card><h3>Server</h3>
   <label>Model (GGUF path)</label><input id=model placeholder="~/AI-Models/...">
   <label>llama-server binary</label><input id=bin>
   <div class=row><div><label>Host</label><input id=host value=127.0.0.1></div><div><label>Port</label><input id=port value=8080 type=number></div></div>
   <div class=row><div><label>Ctx</label><input id=ctx value=4096 type=number></div><div><label>GPU layers (-ngl)</label><input id=ngl value=-1 type=number></div></div>
   <label>mmproj (optional, vision)</label><input id=mmproj placeholder="path to mmproj*.gguf">
   <p><button onclick="act('start')">Start</button><button onclick="act('stop')">Stop</button><button onclick="refresh()">Refresh</button></p>
   <label>Presets</label>
   <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap"><select id=preset onchange="applyPreset()" style="flex:1;min-width:180px"><option value="">—</option></select>
   <button onclick="startPreset()">Start preset</button><button onclick="savePreset()">Save</button><button onclick="renamePreset()">Rename</button><button onclick="deletePreset()">Delete</button></div>
   <div id=st>—</div>
 </div>
</div>
<div class=card style="margin-top:12px"><h3>Models in models_dir <small id=mcount></small></h3><div id=models style="max-height:240px;overflow:auto">loading…</div></div>
<div class=card style="margin-top:12px"><h3>Chat test (via /v1/chat/completions)</h3>
 <input id=prompt placeholder="Say hello…" value="你好，请用一句话介绍你自己。">
 <p><button onclick="chat()">Send</button></p>
 <pre id=chatout style="max-height:180px"></pre>
</div>
<div class=card style="margin-top:12px"><h3>Server log tail</h3><pre id=log></pre></div>
<script>
async function j(u,o){const r=await fetch(u,o);const t=await r.text();try{return JSON.parse(t)}catch(e){return {error:t}}}
async function refresh(){
 const s=await j('/api/status'); const hw=await j('/api/hardware'); const ms=await j('/api/models'); const cfg=await j('/api/config');
 if(cfg&&!cfg.error){bin.value=cfg.llama_server||''; host.value=cfg.host; port.value=cfg.port; ctx.value=cfg.ctx_size; ngl.value=cfg.n_gpu_layers; mmproj.value=cfg.mmproj||mmproj.value||''; if(!model.value&&s.model) model.value=s.model; const ps=(cfg.presets||[]); preset.innerHTML='<option value="">—</option>'+ps.map((p,i)=>`<option value="${i}">${p.name||p.model||i}</option>`).join('');}
 if(hw&&!hw.error){hwEl=hw; document.getElementById('hw').innerHTML=`${hw.cpu}<br>RAM ${hw.ram_gb} GB, cores ${hw.cores||'?'}<br>GPU ${hw.gpu} (Metal: ${hw.metal})<br><small>${hw.os} ${hw.arch}</small>`}
 if(s&&!s.error){const ok=s.healthy?'<span class=ok>healthy</span>':(s.running?'<span class=bad>starting/unhealthy</span>':'stopped'); document.getElementById('st').innerHTML=`${ok} pid=${s.pid||'-'} port=${s.port||'-'}<br><small>${s.model||''}</small>`; document.getElementById('log').textContent=(s.log_tail||[]).join('\n')}
 if(ms&&!ms.error){document.getElementById('mcount').textContent=`(${ms.length})`; document.getElementById('models').innerHTML='<table><tr><th></th><th>name</th><th>GB</th><th>path</th></tr>'+ms.map(m=>`<tr><td><button onclick="pick(${JSON.stringify(m.path)})">use</button></td><td>${m.name}</td><td>${m.size_gb}</td><td><small>${m.path}</small></td></tr>`).join('')+'</table>'}
}
function pick(p){model.value=p}
async function act(a){
 if(a==='start'){const r=await j('/api/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({model:model.value,llama_server:bin.value,host:host.value,port:+port.value,ctx_size:+ctx.value,n_gpu_layers:+ngl.value,mmproj:mmproj.value||null})}); if(r.error) alert(r.error)}
 else{const r=await j('/api/stop',{method:'POST'}); if(r.error) alert(r.error)}
 setTimeout(refresh,600)
}

function applyPreset(){const i=preset.value; if(i==='')return; fetch('/api/config').then(r=>r.json()).then(c=>{const p=(c.presets||[])[+i]; if(!p)return; if(p.model)model.value=p.model; if(p.mmproj!=null)mmproj.value=p.mmproj||''; if(p.ctx_size)ctx.value=p.ctx_size; if(p.n_gpu_layers!=null)ngl.value=p.n_gpu_layers; if(p.port)port.value=p.port; if(p.host)host.value=p.host;});}
async function startPreset(){const i=preset.value; if(i===''){alert('Select a preset');return;} const r=await j('/api/preset/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({index:+i})}); if(r.error) alert(r.error); setTimeout(refresh,800);}
async function savePreset(){const name=prompt('Preset name', (model.value.split('/').pop()||'preset')); if(!name)return; const r=await j('/api/preset',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,model:model.value,mmproj:mmproj.value||null,ctx_size:+ctx.value,n_gpu_layers:+ngl.value,port:+port.value,host:host.value})}); if(r.error) alert(r.error); refresh();}
async function renamePreset(){const i=preset.value; if(i===''){alert('Select a preset');return;} const name=prompt('New name'); if(!name)return; const r=await j('/api/preset/rename',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({index:+i,name})}); if(r.error) alert(r.error); refresh();}
async function deletePreset(){const i=preset.value; if(i===''){alert('Select a preset');return;} if(!confirm('Delete preset?'))return; const r=await j('/api/preset/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({index:+i})}); if(r.error) alert(r.error); refresh();}


async function exportPresets(){const c=await j('/api/config'); const b=new Blob([JSON.stringify(c.presets||[],null,2)],{type:'application/json'}); const a=document.createElement('a'); a.href=URL.createObjectURL(b); a.download='localmodelpilot-presets.json'; a.click();}
async function importPresets(){const t=prompt('Paste presets JSON array'); if(!t)return; let data; try{data=JSON.parse(t)}catch(e){alert('Invalid JSON');return;} const r=await j('/api/preset/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({presets:data})}); if(r.error) alert(r.error); refresh();}

async function chat(){
 chatout.textContent='…';
 const st=await j('/api/status'); const host=st.host||'127.0.0.1', port=st.port||8080;
 try{
  const r=await fetch(`http://${host}:${port}/v1/chat/completions`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({messages:[{role:'user',content:prompt.value}],max_tokens:200,stream:false})});
  const t=await r.json(); chatout.textContent=(t.choices&&t.choices[0]&&(t.choices[0].message?.content||t.choices[0].text))||JSON.stringify(t,null,2);
 }catch(e){ chatout.textContent=String(e)+' (ensure server running & CORS allows file/app origin; if blocked, test via curl)'; }
}
refresh(); setInterval(refresh, 4000);
</script>
"""


class H(BaseHTTPRequestHandler):
    def _send(self, code, obj, ctype="application/json; charset=utf-8"):
        body = obj if isinstance(obj, (bytes, bytearray)) else json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):  # quiet (avoid log spam / disk writes)
        return

    def do_GET(self):
        p = urlparse(self.path).path
        cfg = load_config()
        if p == "/": return self._send(200, INDEX.encode(), "text/html; charset=utf-8")
        if p == "/api/hardware": return self._send(200, asdict_hw(scan_hardware()))
        if p == "/api/models": return self._send(200, to_dicts(scan_models(cfg.models_dir)))
        if p == "/api/status":
            st = status(cfg); return self._send(200, st.__dict__)
        if p == "/api/config": return self._send(200, cfg.__dict__)
        self._send(404, {"error": "not found"})

    def do_POST(self):
        p = urlparse(self.path).path
        try:
            n = int(self.headers.get("Content-Length") or 0)
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            data = {}
        cfg = load_config()
        try:
            if p == "/api/start":
                if data.get("llama_server"): cfg.llama_server = data["llama_server"]; save_config(cfg)
                st = start_server(cfg, data.get("model",""), host=data.get("host"), port=data.get("port"),
                                  ctx_size=data.get("ctx_size"), n_gpu_layers=data.get("n_gpu_layers"), mmproj=data.get("mmproj"))
                return self._send(200, st.__dict__)
            if p == "/api/stop":
                return self._send(200, stop_server(cfg).__dict__)
            if p == "/api/preset":
                cfg.presets = list(getattr(cfg,"presets",[]) or [])
                data.pop("llama_server", None)
                idx = data.pop("index", None)
                if idx is not None and 0 <= int(idx) < len(cfg.presets):
                    old = cfg.presets[int(idx)]; old.update({k:v for k,v in data.items() if v is not None}); cfg.presets[int(idx)] = old
                else:
                    cfg.presets = [x for x in cfg.presets if x.get("name")!=data.get("name")] + [data]
                save_config(cfg); return self._send(200, {"ok":True,"presets":cfg.presets})
            if p == "/api/preset/rename":
                cfg.presets = list(getattr(cfg,"presets",[]) or []); i=int(data.get("index",-1))
                if not (0 <= i < len(cfg.presets)): return self._send(400,{"error":"bad index"})
                cfg.presets[i]["name"]=str(data.get("name") or cfg.presets[i].get("name") or "preset")
                save_config(cfg); return self._send(200, {"ok":True,"presets":cfg.presets})
            if p == "/api/preset/delete":
                cfg.presets = list(getattr(cfg,"presets",[]) or []); i=int(data.get("index",-1))
                if not (0 <= i < len(cfg.presets)): return self._send(400,{"error":"bad index"})
                cfg.presets.pop(i); save_config(cfg); return self._send(200, {"ok":True,"presets":cfg.presets})
            if p == "/api/preset/start":
                cfg.presets = list(getattr(cfg,"presets",[]) or []); i=int(data.get("index",-1))
                if not (0 <= i < len(cfg.presets)): return self._send(400,{"error":"bad index"})
                pr=cfg.presets[i]
                st=start_server(cfg, pr.get("model",""), host=pr.get("host"), port=pr.get("port"), ctx_size=pr.get("ctx_size"), n_gpu_layers=pr.get("n_gpu_layers"), threads=pr.get("threads"), mmproj=pr.get("mmproj"))
                return self._send(200, st.__dict__)
            if p == "/api/preset/import":
                inc=data.get("presets", data)
                if isinstance(inc, dict): inc=inc.get("presets",[inc])
                ps=list(getattr(cfg,"presets",[]) or []); by={p.get("name"):p for p in ps}
                for pr in inc:
                    if isinstance(pr,dict) and pr.get("name"): by[pr["name"]]=pr
                cfg.presets=list(by.values()); save_config(cfg); return self._send(200,{"ok":True,"presets":cfg.presets})
        except Exception as e:
            return self._send(400, {"error": str(e)})
        self._send(404, {"error": "not found"})


def serve(cfg):
    httpd = ThreadingHTTPServer((cfg.web_host, cfg.web_port), H)
    print(f"LocalModelPilot UI: http://{cfg.web_host}:{cfg.web_port}")
    httpd.serve_forever()
