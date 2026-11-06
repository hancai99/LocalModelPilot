from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass, asdict

MODEL_EXTS = {".gguf", ".safetensors", ".bin", ".pth", ".pt"}


@dataclass
class ModelFile:
    path: str
    name: str
    size_bytes: int
    ext: str

    @property
    def size_gb(self) -> float:
        return round(self.size_bytes / (1024**3), 3)


def scan_models(models_dir: str | Path) -> list[ModelFile]:
    root = Path(models_dir).expanduser()
    if not root.exists():
        return []
    items: list[ModelFile] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() in MODEL_EXTS and not p.name.endswith(".part"):
            try:
                st = p.stat()
            except OSError:
                continue
            items.append(ModelFile(path=str(p), name=p.name, size_bytes=st.st_size, ext=p.suffix.lower()))
    items.sort(key=lambda m: (m.ext != ".gguf", -m.size_bytes, m.name.lower()))
    return items


def to_dicts(models: list[ModelFile]) -> list[dict]:
    out = []
    for m in models:
        d = asdict(m); d["size_gb"] = m.size_gb; out.append(d)
    return out
