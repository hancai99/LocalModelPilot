from __future__ import annotations
import plistlib, sys
from pathlib import Path

LABEL = "local.localmodelpilot.webui"
PLIST = Path.home() / "Library/LaunchAgents" / f"{LABEL}.plist"


def _program_args() -> list[str]:
    # Prefer installed app executable if present, else current python -m
    app = Path.home() / "LocalModelPilot/dist/LocalModelPilot.app/Contents/MacOS/LocalModelPilot"
    if app.is_file():
        return [str(app), "web"]
    return [sys.executable, "-m", "localmodelpilot", "web"]


def install() -> str:
    PLIST.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "Label": LABEL,
        "ProgramArguments": _program_args(),
        "RunAtLoad": True,
        "KeepAlive": False,
        "StandardOutPath": str(Path.home() / "Library/Logs/LocalModelPilot/launchd.out.log"),
        "StandardErrorPath": str(Path.home() / "Library/Logs/LocalModelPilot/launchd.err.log"),
    }
    PLIST.write_bytes(plistlib.dumps(data))
    return f"wrote {PLIST} (run: launchctl bootstrap gui/$UID {PLIST} to load now; or log out/in)"


def uninstall() -> str:
    if PLIST.exists():
        PLIST.unlink()
        return f"removed {PLIST} (run: launchctl bootout gui/$UID/{LABEL} to stop now, if loaded)"
    return f"not installed ({PLIST})"
