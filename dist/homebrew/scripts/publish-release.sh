#!/bin/zsh
# Publish LocalModelPilot release artifacts via GitHub CLI.
set -euo pipefail
VER="${1:-0.1.0}"
TAG="v${VER}"
REPO="${REPO:-}"
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"   # .../LocalModelPilot
DIST="$ROOT/dist"
files=("$DIST/LocalModelPilot-${VER}.dmg" "$DIST/LocalModelPilot-${VER}-standalone-macos.zip" "$DIST/LocalModelPilot-${VER}-source.zip" "$DIST/SHA256SUMS.txt" "$DIST/RELEASE_NOTES.md")
for f in "${files[@]}"; do [[ -f "$f" ]] || { echo "missing: $f"; exit 1; }; done
cmd=(gh release create "$TAG" "${files[@]}" --title "LocalModelPilot ${VER}" --notes-file "$DIST/RELEASE_NOTES.md")
[[ -n "$REPO" ]] && cmd+=(--repo "$REPO")
echo "+ ${cmd[*]}"; "${cmd[@]}"
echo "url: https://github.com/${REPO:-<OWNER>/<REPO>}/releases/download/${TAG}/LocalModelPilot-${VER}.dmg"
