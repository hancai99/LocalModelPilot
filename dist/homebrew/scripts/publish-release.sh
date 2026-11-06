#!/bin/zsh
# Publish LocalModelPilot release artifacts via GitHub CLI.
# Prereqs: gh auth login; repo exists; artifacts in ../ (dist/) are current.
set -euo pipefail
VER="${1:-0.1.0}"
TAG="v${VER}"
REPO="${REPO:-}"   # optional: OWNER/REPO; else uses current git remote
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIST="$ROOT/dist"

files=(
  "$DIST/LocalModelPilot-${VER}.dmg"
  "$DIST/LocalModelPilot-${VER}-standalone-macos.zip"
  "$DIST/LocalModelPilot-${VER}-source.zip"
  "$DIST/SHA256SUMS.txt"
  "$DIST/RELEASE_NOTES.md"
)
for f in "${files[@]}"; do [[ -f "$f" ]] || { echo "missing: $f"; exit 1; }; done

cmd=(gh release create "$TAG" "${files[@]}" --title "LocalModelPilot ${VER}" --notes-file "$DIST/RELEASE_NOTES.md")
[[ -n "$REPO" ]] && cmd+=(--repo "$REPO")
echo "+ ${cmd[*]}"
"${cmd[@]}"

echo "Done. Update homebrew cask url to:"
echo "  https://github.com/<OWNER>/<REPO>/releases/download/${TAG}/LocalModelPilot-${VER}.dmg"
echo "And refresh sha256 from dist/SHA256SUMS.txt"
