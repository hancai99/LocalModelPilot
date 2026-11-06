cask "localmodelpilot" do
  version "0.1.0"
  sha256 "0df84d53eabec32948847e99bd258bb3488e49f6e9320f10918efe78461db6b1"

  # TODO: replace with your published release URL (GitHub Releases recommended)
  # url "https://github.com/<OWNER>/<REPO>/releases/download/v#{version}/LocalModelPilot-#{version}.dmg"
  url "file://#{Dir.home}/LocalModelPilot/dist/LocalModelPilot-#{version}.dmg"
  name "LocalModelPilot"
  desc "Local model helper for macOS (llama-server control, GGUF catalog, Web UI)"
  homepage "https://github.com/<OWNER>/<REPO>"

  depends_on macos: ">= :monterey"

  app "LocalModelPilot.app"

  zap trash: [
    "~/Library/Application Support/LocalModelPilot",
    "~/Library/Logs/LocalModelPilot",
    "~/Library/LaunchAgents/local.localmodelpilot.webui.plist",
  ]

  caveats <<~EOS
    LocalModelPilot reuses an existing llama-server binary and local model files (e.g. ~/AI-Models).
    Ad-hoc signed build: if macOS blocks it, run:
      xattr -dr com.apple.quarantine /Applications/LocalModelPilot.app
    For public distribution, configure Developer ID signing + notarization and publish a GitHub Release URL.
  EOS
end
