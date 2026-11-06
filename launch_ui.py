from localmodelpilot.__main__ import main
import sys
# Default to web UI when launched as app bundle
if len(sys.argv) == 1:
    sys.argv = [sys.argv[0], "web"]
raise SystemExit(main())
