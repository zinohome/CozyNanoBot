FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# git + patch 用于套 patch；curl 用于 healthcheck
RUN apt-get update \
    && apt-get install -y --no-install-recommends git patch curl \
    && rm -rf /var/lib/apt/lists/*

# 非 root 用户
RUN groupadd --system --gid 1001 cozy \
    && useradd  --system --uid 1001 --gid cozy --home-dir /app --shell /usr/sbin/nologin cozy

WORKDIR /app

# --- 源码拷贝 ---
COPY upstream/nanobot /app/upstream/nanobot
COPY pyproject.toml   /app/
COPY src              /app/src
COPY config           /app/config
COPY patches          /app/patches
COPY scripts          /app/scripts
# ★ skills/ 需落到 workspace/skills/（nanobot 首次启动会在 ~/.cozy-nanobot/workspace/ 初始化）
COPY skills           /app/.cozy-nanobot/workspace/skills

# --- 套 patch（容器内执行，保证镜像包含补丁；idempotent：已套则跳过）---
# 不依赖 git repo：用 patch(1) 的 --dry-run 探测已套过的 patch
RUN set -eux; \
    cd upstream/nanobot; \
    for p in /app/patches/*.patch; do \
        if patch -p1 --dry-run --silent --reverse < "$p" >/dev/null 2>&1; then \
            echo "[patch] already applied: $(basename "$p")"; \
        else \
            echo "[patch] applying: $(basename "$p")"; \
            patch -p1 < "$p"; \
        fi; \
    done; \
    touch /app/.patches-applied

# --- Python 依赖安装 ---
RUN pip install -e upstream/nanobot && pip install -e .

# 权限交给非 root 用户
RUN chown -R cozy:cozy /app

USER cozy

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8080/health || exit 1

CMD ["nanobot", "serve", "-c", "/app/config/nanobot.yaml", "--host", "0.0.0.0", "--port", "8080"]
