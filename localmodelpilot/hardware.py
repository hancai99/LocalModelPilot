from __future__ import annotations
import platform, subprocess, shutil
from dataclasses import dataclass, asdict


@dataclass
class Hardware:
    os: str
    arch: str
    cpu: str
    ram_gb: float
    gpu: str
    metal: bool
    cores: int | None


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, timeout=5).strip()
    except Exception:
        return ""


def scan_hardware() -> Hardware:
    cpu = _run(["sysctl", "-n", "machdep.cpu.brand_string"]) or platform.processor() or "unknown"
    mem = _run(["sysctl", "-n", "hw.memsize"])
    ram_gb = round(int(mem) / (1024**3), 1) if mem.isdigit() else 0.0
    cores_s = _run(["sysctl", "-n", "hw.logicalcpu"])
    cores = int(cores_s) if cores_s.isdigit() else None
    gpu = ""
    metal = False
    sp = _run(["system_profiler", "SPDisplaysDataType"])
    for line in sp.splitlines():
        if "Chipset Model:" in line and not gpu:
            gpu = line.split(":", 1)[1].strip()
        if "Metal Support:" in line and "Metal" in line:
            metal = True
    return Hardware(os=f"{platform.system()} {platform.release()}", arch=platform.machine(),
                    cpu=cpu, ram_gb=ram_gb, gpu=gpu or "unknown", metal=metal, cores=cores)


def recommend(ram_gb: float, file_size_gb: float | None = None) -> dict:
    # Conservative heuristic for Apple Silicon unified memory (reserve ~6GB for system+context overhead)
    budget = max(ram_gb - 6.0, 2.0)
    fits = None if file_size_gb is None else file_size_gb <= budget
    tip = "Use Metal (-ngl 999). Prefer Q4_K_M/Q3_K for tighter memory; raise ctx only if RAM allows."
    return {"ram_gb": ram_gb, "est_model_budget_gb": round(budget, 1),
            "file_size_gb": file_size_gb, "fits_estimate": fits, "tip": tip}


def asdict_hw(hw: Hardware) -> dict:
    return asdict(hw)
