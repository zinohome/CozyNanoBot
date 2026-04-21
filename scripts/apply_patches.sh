#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
UPSTREAM="$HERE/upstream/nanobot"
PATCHES="$HERE/patches"
MARKER="$HERE/.patches-applied"

if [[ ! -d "$UPSTREAM" ]]; then
    echo "upstream/nanobot missing; run 'git submodule update --init'" >&2
    exit 1
fi

if [[ -f "$MARKER" ]]; then
    echo "patches already applied"
    exit 0
fi

cd "$UPSTREAM"

if ! compgen -G "$PATCHES/*.patch" > /dev/null; then
    echo "no patches"
    touch "$MARKER"
    exit 0
fi

for p in "$PATCHES"/*.patch; do
    echo "Applying $(basename "$p")..."
    git apply --check "$p"
    git apply "$p"
done

touch "$MARKER"
echo "All patches applied."
