from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from .config import load_config, save_config, CONFIG_PATH
from .hardware import scan_hardware, recommend, asdict_hw
from .models import scan_models, to_dicts
from .server import start_server, stop_server, status
from .webui import serve
from .loginitem import install as li_install, uninstall as li_uninstall, PLIST as LI_PLIST


def jprint(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="localmodelpilot", description="Local model helper (macOS)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("scan", help="scan hardware")
    pmodels = sub.add_parser("models", help="list model files")
    pmodels.add_argument("--dir", dest="dir_", default=None)

    ps = sub.add_parser("serve", help="start llama-server for a model")
    ps.add_argument("--model", "-m", required=True)
    ps.add_argument("--host"); ps.add_argument("--port", type=int)
    ps.add_argument("--ctx", type=int, dest="ctx_size"); ps.add_argument("--ngl", type=int, dest="n_gpu_layers")
    ps.add_argument("--threads", type=int)
    ps.add_argument("--mmproj", help="multimodal projector file (vision)")
    ps.add_argument("--llama-server", dest="llama_server")

    sub.add_parser("stop", help="stop managed llama-server")
    sub.add_parser("status", help="show llama-server status")
    sub.add_parser("config", help="show config path and values")
    sub.add_parser("web", help="start local web UI")
    pli=sub.add_parser("loginitem", help="opt-in LaunchAgent for web UI")
    pli.add_argument("action", choices=["install","uninstall","status"])
    pp=sub.add_parser("preset", help="manage and start presets")
    pp.add_argument("action", choices=["list","start","delete","rename","export","import"])
    pp.add_argument("name", nargs="?")
    pp.add_argument("--to", dest="to_name")
    pp.add_argument("--file","-f", dest="file")

    a = ap.parse_args(argv)
    cfg = load_config()

    if a.cmd == "scan":
        hw = scan_hardware(); rec = recommend(hw.ram_gb)
        jprint({"hardware": asdict_hw(hw), "recommendation": rec})
    elif a.cmd == "models":
        ms = scan_models(a.dir_ or cfg.models_dir)
        jprint({"models_dir": a.dir_ or cfg.models_dir, "count": len(ms), "models": to_dicts(ms)})
    elif a.cmd == "serve":
        if a.llama_server: cfg.llama_server = a.llama_server; save_config(cfg)
        st = start_server(cfg, a.model, host=a.host, port=a.port, ctx_size=a.ctx_size,
                          n_gpu_layers=a.n_gpu_layers, threads=a.threads, mmproj=getattr(a,"mmproj",None))
        jprint({"started": st.__dict__, "note": f"llama-server on http://{st.host}:{st.port} (if healthy)"})
    elif a.cmd == "stop":
        jprint(stop_server(cfg).__dict__)
    elif a.cmd == "status":
        jprint(status(cfg).__dict__)
    elif a.cmd == "config":
        jprint({"path": str(CONFIG_PATH), "config": cfg.__dict__})
    elif a.cmd == "web":
        serve(cfg)
    elif a.cmd == "loginitem":
        if a.action=="install": print(li_install())
        elif a.action=="uninstall": print(li_uninstall())
        else: print(json.dumps({"plist":str(LI_PLIST),"exists":LI_PLIST.exists()}, indent=2))
    elif a.cmd == "preset":
        ps = list(getattr(cfg,"presets",[]) or [])
        def find(name):
            for i,p in enumerate(ps):
                if p.get("name")==name or str(i)==name: return i,p
            raise SystemExit(f"preset not found: {name}")
        if a.action=="list": jprint({"count":len(ps),"presets":ps})
        elif a.action=="delete":
            i,_=find(a.name or ""); ps.pop(i); cfg.presets=ps; save_config(cfg); jprint({"ok":True,"presets":ps})
        elif a.action=="rename":
            i,p=find(a.name or ""); p["name"]=a.to_name or p["name"]; ps[i]=p; cfg.presets=ps; save_config(cfg); jprint({"ok":True,"preset":p})
        elif a.action=="start":
            i,p=find(a.name or ""); st=start_server(cfg,p.get("model",""),host=p.get("host"),port=p.get("port"),ctx_size=p.get("ctx_size"),n_gpu_layers=p.get("n_gpu_layers"),threads=p.get("threads"),mmproj=p.get("mmproj")); jprint(st.__dict__)
        elif a.action=="export":
            fp = Path(a.file or "presets.json").expanduser()
            fp.write_text(json.dumps(ps, indent=2, ensure_ascii=False))
            jprint({"ok":True,"file":str(fp),"count":len(ps)})
        elif a.action=="import":
            fp = Path(a.file or a.name or "presets.json").expanduser()
            inc = json.loads(fp.read_text())
            if isinstance(inc, dict): inc = inc.get("presets", [inc])
            by = {p.get("name"): p for p in ps}
            for p in inc:
                if isinstance(p, dict) and p.get("name"): by[p["name"]] = p
            cfg.presets = list(by.values()); save_config(cfg)
            jprint({"ok":True,"file":str(fp),"count":len(cfg.presets)})
    else:
        ap.print_help(); return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
