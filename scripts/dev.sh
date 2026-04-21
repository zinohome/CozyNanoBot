#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$HERE"
bash scripts/apply_patches.sh
exec .venv/bin/nanobot serve --config config/nanobot.yaml --verbose
