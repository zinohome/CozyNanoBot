#!/usr/bin/env bash
# CozyNanoBot Base Runtime 镜像构建脚本
# 构建 cozy-nanobot:latest，包含：
#   1) upstream/nanobot submodule 代码
#   2) 已套好的 Cozy patch（在 Dockerfile RUN 阶段完成，idempotent）
#   3) 我们的 MCP tools（src/cozy_mcp_tools/）
#
# 用法：
#   bash deploy/base_runtime/build.sh
#
# 前置条件：
#   - 宿主机已装 docker、git
#   - 已执行 `git submodule update --init --recursive`（脚本会尝试自动执行）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo -e "${GREEN}[BUILD]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

cd "$REPO_ROOT"

# 1) 初始化 submodule（幂等）
if [[ ! -f upstream/nanobot/pyproject.toml ]]; then
    log "Initializing git submodule upstream/nanobot ..."
    git submodule update --init --recursive
else
    log "Submodule upstream/nanobot already present, skipping init."
fi

# 2) 若 upstream 已有本地改动（例如之前手工套过 patch），回滚到干净 HEAD
#    这样 Dockerfile 内的 patch 步骤会在干净源码上执行，避免重复。
if [[ -d upstream/nanobot/.git ]] || [[ -f upstream/nanobot/.git ]]; then
    if ! git -C upstream/nanobot diff --quiet || ! git -C upstream/nanobot diff --cached --quiet; then
        warn "upstream/nanobot 有本地改动，重置为干净 HEAD ..."
        git -C upstream/nanobot reset --hard HEAD
        git -C upstream/nanobot clean -fd
    fi
fi

# 3) docker build — 上下文为仓库根目录；Dockerfile 内的 RUN 会套 patch（idempotent）
log "Running docker build ..."
docker build \
    -f "$REPO_ROOT/Dockerfile" \
    -t cozy-nanobot:latest \
    "$REPO_ROOT"

log "Done. cozy-nanobot:latest built."
docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" \
    | grep -E "REPOSITORY|cozy-nanobot" || true
