# LocalModelPilot 0.1.0 (macOS, 2026-11-06)

Original local model helper (not a LocModel copy). Reuses existing `llama-server` and local model files.

## Features
- Hardware scan (Apple Silicon/Metal/RAM) + capacity heuristic.
- GGUF/model catalog for `~/AI-Models`.
- Start/stop/status for `llama-server` (host/port/ctx/`-ngl`/threads/extra args).
- **Multimodal**: `--mmproj` / Web UI mmproj field (autodetects `mmproj-BF16.gguf` when present).
- Web UI with chat test (`/v1/chat/completions`).
- Safety: atomic config writes; 5 MiB log cap + rotation; 256 KiB/s subprocess-log rate limit.

## Artifacts & verification
- `LocalModelPilot-0.1.0.dmg` (recommended), `LocalModelPilot-0.1.0-standalone-macos.zip`, `LocalModelPilot-0.1.0-source.zip`
- Verify: `shasum -a 256 -c dist/SHA256SUMS.txt`

## Notes
- Ad-hoc signed build; distributing to other Macs may require Gatekeeper override or Developer ID signing + notarization (`codesign`/`notarytool`, Apple Developer cert required).
- Bundles do not include model weights or `llama-server` binaries.

## Publishing
```bash
# after gh auth login and setting git remote / REPO=OWNER/REPO
~/LocalModelPilot/dist/homebrew/scripts/publish-release.sh 0.1.0
```
Then update `dist/homebrew/Casks/localmodelpilot.rb` `url/homepage/sha256` to the GitHub Release values.
