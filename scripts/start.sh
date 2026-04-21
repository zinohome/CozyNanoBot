#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$HERE"

# 套 patch
bash scripts/apply_patches.sh

# 启动
exec .venv/bin/nanobot serve \
    --config config/nanobot.yaml \
    --host "${HOST:-0.0.0.0}" \
    --port "${PORT:-8080}"
