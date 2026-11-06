# Homebrew tap/cask metadata (LocalModelPilot)

`Casks/localmodelpilot.rb` is a template. Current `sha256` matches `dist/LocalModelPilot-0.1.0.dmg`; `url` points to a local file for testing.

## Publish (recommended)
1. Create a GitHub repo and push this project (or release artifacts).
2. Create a Release `v0.1.0` and upload `LocalModelPilot-0.1.0.dmg`.
3. Update `url` and `homepage` in the cask to the GitHub Release URLs.
4. Create a tap repo named `homebrew-<tap>` and copy `Casks/localmodelpilot.rb` into `Casks/`.

## Install
```bash
# local test (from this folder)
brew install --cask ./Casks/localmodelpilot.rb

# after publishing a tap
# brew tap <OWNER>/<tap>
# brew install --cask localmodelpilot
```

## Notes
- Ad-hoc signed/notarization not complete (needs Apple Developer ID). Public users may need `xattr -dr com.apple.quarantine`.
- Cask installs the `.app` only; it does not bundle model weights or `llama-server`.
