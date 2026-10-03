#!/usr/bin/env bash
#
# install.sh - words.py has no dependencies, so there is nothing to install.
# This script verifies the one prerequisite (Python 3.9+) and the shipped file,
# then exits. It never needs sudo, never installs a system package, never
# writes a config file and never starts a server.
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "install.sh: '$PYTHON' not found. Install Python 3.9 or newer, or set PYTHON=/path/to/python3." >&2
  exit 1
fi

if ! "$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)'; then
  echo "install.sh: Python 3.9 or newer is required; '$PYTHON' is $("$PYTHON" -c 'import sys; print(sys.version.split()[0])')." >&2
  exit 1
fi

"$PYTHON" -c 'import words' || {
  echo "install.sh: words.py could not be imported; the checkout looks damaged." >&2
  exit 1
}

"$PYTHON" words.py sample.txt >/dev/null || {
  echo "install.sh: smoke test failed (sample.txt should count cleanly)." >&2
  exit 1
}

echo "Setup complete: no packages to install, nothing to configure."
echo "Run it:  $PYTHON words.py <file>"
echo "Demo:    bash demo.sh"
echo "Tests:   $PYTHON -m unittest test_words -v"
