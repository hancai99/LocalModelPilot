from __future__ import annotations
import os, time
from pathlib import Path

MAX_LOG_BYTES = 5 * 1024 * 1024  # 5 MiB cap (prevents runaway disk writes)
RATE_BYTES_PER_SEC = 256 * 1024   # persist at most 256 KiB/s of subprocess output


class CappedRateLogger:
    def __init__(self, path: Path):
        self.path = path
        self._win_start = time.monotonic()
        self._win_bytes = 0
        self._dropped = 0

    def _rotate_if_needed(self):
        try:
            if self.path.exists() and self.path.stat().st_size >= MAX_LOG_BYTES:
                old = self.path.with_suffix(self.path.suffix + ".1")
                try: os.replace(self.path, old)
                except OSError: self.path.unlink(missing_ok=True)
        except OSError:
            pass

    def write_line(self, line: str):
        now = time.monotonic()
        if now - self._win_start >= 1.0:
            self._win_start = now
            self._win_bytes = 0
            self._dropped = 0
        b = (line.rstrip("\n") + "\n").encode("utf-8", "replace")
        if self._win_bytes + len(b) > RATE_BYTES_PER_SEC:
            self._dropped += 1
            if self._dropped in (1, 100, 1000) or self._dropped % 5000 == 0:
                b = f"[localmodelpilot] log rate-limited, dropped {self._dropped} lines\n".encode()
            else:
                return
        self._win_bytes += len(b)
        self._rotate_if_needed()
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("ab") as f:
                f.write(b)
        except OSError:
            pass
