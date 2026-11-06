from __future__ import annotations
import json, os, signal, subprocess, threading, time, urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from .config import Config, PID_PATH, STATE_PATH, LOG_PATH, ensure_dirs
from .logutil import CappedRateLogger

TAIL_MAX = 400


@dataclass
class ServerStatus:
    running: bool
    pid: int | None
    model: str | None
    host: str | None
    port: int | None
    healthy: bool | None
    cmd: list[str] | None
    log_tail: list[str]


_proc: subprocess.Popen | None = None
_tail: list[str] = []
_lock = threading.Lock()
_logger = CappedRateLogger(LOG_PATH)


def _append(line: str):
    with _lock:
        _tail.append(line.rstrip("\n"))
        if len(_tail) > TAIL_MAX:
            del _tail[: len(_tail) - TAIL_MAX]
    _logger.write_line(line)


def _pump(stream, prefix: str):
    try:
        for raw in iter(stream.readline, b""):
            try:
                _append(f"{prefix}{raw.decode('utf-8','replace')}")
            except Exception:
                pass
    except Exception:
        pass
    finally:
        try: stream.close()
        except Exception: pass


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0); return True
    except OSError:
        return False


def _http_ok(url: str, timeout: float = 1.5) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return 200 <= r.status < 500
    except Exception:
        return False


def start_server(cfg: Config, model: str, *, host: str | None = None, port: int | None = None,
                 ctx_size: int | None = None, n_gpu_layers: int | None = None, threads: int | None = None, mmproj: str | None = None,
                 extra_args: list[str] | None = None) -> ServerStatus:
    global _proc
    if not cfg.llama_server or not Path(cfg.llama_server).is_file():
        raise FileNotFoundError(f"llama-server not found: {cfg.llama_server!r}. Set config.llama_server.")
    mp = Path(model).expanduser()
    if not mp.is_file():
        raise FileNotFoundError(f"Model not found: {mp}")
    st = status(cfg)
    if st.running and st.pid:
        raise RuntimeError(f"Server already running (pid {st.pid}). Stop it first.")
    h = host or cfg.host
    p = int(port or cfg.port)
    cmd = [cfg.llama_server, "-m", str(mp), "--host", h, "--port", str(p)]
    ctx = ctx_size if ctx_size is not None else cfg.ctx_size
    if ctx and ctx > 0: cmd += ["-c", str(ctx)]
    ngl = n_gpu_layers if n_gpu_layers is not None else cfg.n_gpu_layers
    if ngl is not None: cmd += ["-ngl", str(ngl)]
    th = threads if threads is not None else cfg.threads
    if th and th > 0: cmd += ["-t", str(th)]
    mm = mmproj if mmproj is not None else getattr(cfg, "mmproj", None)
    if mm and Path(mm).expanduser().is_file(): cmd += ["--mmproj", str(Path(mm).expanduser())]
    cmd += (extra_args if extra_args is not None else (cfg.extra_args or []))

    ensure_dirs()
    with _lock:
        _tail.clear()
    _append(f"[start] {' '.join(cmd)}")
    _proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    PID_PATH.write_text(str(_proc.pid))
    STATE_PATH.write_text(json.dumps({"pid": _proc.pid, "model": str(mp), "host": h, "port": p, "cmd": cmd}))
    threading.Thread(target=_pump, args=(_proc.stdout, ""), daemon=True).start()
    threading.Thread(target=_pump, args=(_proc.stderr, ""), daemon=True).start()
    return status(cfg)


def stop_server(cfg: Config) -> ServerStatus:
    global _proc
    pid = None
    if _proc and _proc.poll() is None:
        pid = _proc.pid
        _proc.terminate()
        try: _proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            _proc.kill(); _proc.wait(timeout=3)
    elif PID_PATH.exists():
        try: pid = int(PID_PATH.read_text().strip())
        except Exception: pid = None
        if pid and _alive(pid):
            os.kill(pid, signal.SIGTERM)
            for _ in range(40):
                if not _alive(pid): break
                time.sleep(0.2)
            if _alive(pid): os.kill(pid, signal.SIGKILL)
    PID_PATH.unlink(missing_ok=True)
    _append(f"[stop] pid={pid}")
    _proc = None
    return status(cfg)


def status(cfg: Config) -> ServerStatus:
    global _proc
    pid = _proc.pid if _proc and _proc.poll() is None else None
    model = host = None; port = None; cmd = None
    if STATE_PATH.exists():
        try:
            s = json.loads(STATE_PATH.read_text())
            model, host, port, cmd = s.get("model"), s.get("host"), s.get("port"), s.get("cmd")
        except Exception:
            pass
    if not pid and PID_PATH.exists():
        try:
            p = int(PID_PATH.read_text().strip())
            if _alive(p): pid = p
            else: PID_PATH.unlink(missing_ok=True)
        except Exception:
            pass
    h, p = host or cfg.host, int(port or cfg.port)
    healthy = _http_ok(f"http://{h}:{p}/health") if pid else False
    with _lock:
        tail = list(_tail)
    return ServerStatus(running=bool(pid), pid=pid, model=model, host=h, port=p, healthy=healthy, cmd=cmd, log_tail=tail)
