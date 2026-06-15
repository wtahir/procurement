#!/usr/bin/env bash
# render_build.sh - Build script for Render Python service deployments.

set -euo pipefail

echo "=== [1/2] Upgrading pip ==="
python -m pip install --upgrade pip

echo "=== [2/2] Installing runtime dependencies ==="
pip install -r requirements.txt

echo "=== Build complete ==="
