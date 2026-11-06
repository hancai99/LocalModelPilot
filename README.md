# LocalModelPilot (v0.1, macOS)

Original local model helper: hardware scan, GGUF catalog, and `llama-server` process control.
It **reuses existing `llama-server` binaries** (does not bundle model weights).

## Quick start
```bash
cd ~/LocalModelPilot
python3 -m localmodelpilot scan
python3 -m localmodelpilot models
python3 -m localmodelpilot serve --model ~/AI-Models/<file>.gguf
python3 -m localmodelpilot web   # http://127.0.0.1:8765
```

## Config
`~/Library/Application Support/LocalModelPilot/config.json`
- `models_dir` (default `~/AI-Models`)
- `llama_server` (auto-detected; override path)
- `host`/`port` for llama-server, `web_port` for UI

## Safety
- Atomic config writes, capped log files, no tight write loops.
- Subprocess output is rate-limited when persisted.
