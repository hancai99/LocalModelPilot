from __future__ import annotations
import json, os, shutil, tempfile
from dataclasses import dataclass, asdict
from pathlib import Path

APP_DIR = Path.home() / "Library" / "Application Support" / "LocalModelPilot"
CONFIG_PATH = APP_DIR / "config.json"
STATE_PATH = APP_DIR / "state.json"
LOG_PATH = APP_DIR / "localmodelpilot.log"
PID_PATH = APP_DIR / "llama-server.pid"


def _detect_llama_server() -> str | None:
    candidates = [
        os.environ.get("LLAMA_SERVER"),
        str(Path.home() / "Library/Application Support/LocModel/engines/b12138-metal/llama-b12138/llama-server"),
        shutil.which("llama-server"),
        "/opt/homebrew/bin/llama-server",
    ]
    for c in candidates:
        if c and Path(c).expanduser().is_file() and os.access(c, os.X_OK):
            return str(Path(c).expanduser())
    return None


@dataclass
class Config:
    models_dir: str = str(Path.home() / "AI-Models")
    llama_server: str | None = None
    host: str = "127.0.0.1"
    port: int = 8080
    ctx_size: int = 4096
    n_gpu_layers: int = -1
    threads: int = 0
    web_host: str = "127.0.0.1"
    web_port: int = 8765
    mmproj: str | None = None
    presets: list[dict] = None  # type: ignore[assignment]
    extra_args: list[str] = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.extra_args is None:
            self.extra_args = []
        if self.presets is None:
            self.presets = []
        if not self.llama_server:
            self.llama_server = _detect_llama_server()
        # auto-detect mmproj next to GGUF dir naming pattern if not set (best-effort)
        try:
            if not self.mmproj:
                d = Path(self.models_dir).expanduser()/ "unsloth__Qwen3.6-35B-A3B-GGUF" / "mmproj-BF16.gguf"
                if d.is_file(): self.mmproj = str(d)
        except Exception:
            pass


def ensure_dirs():
    APP_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Config:
    ensure_dirs()
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text())
            base = asdict(Config())
            base.update({k: v for k, v in data.items() if k in base})
            return Config(**base)
        except Exception:
            pass
    c = Config()
    save_config(c)
    return c


def save_config(cfg: Config):
    ensure_dirs()
    data = json.dumps(asdict(cfg), indent=2, ensure_ascii=False)
    fd, tmp = tempfile.mkstemp(dir=str(APP_DIR), prefix=".cfg", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, CONFIG_PATH)
    finally:
        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except OSError:
            pass
