FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY upstream/nanobot /app/upstream/nanobot
COPY pyproject.toml /app/
COPY src /app/src
COPY config /app/config
COPY patches /app/patches
COPY scripts /app/scripts

RUN pip install -e upstream/nanobot && pip install -e .

# 启动前套 patch（Dockerfile 里 upstream 不是 git repo，但 git apply 不需要 repo）
RUN cd upstream/nanobot && for p in ../../patches/*.patch; do git apply "$p" || patch -p1 < "$p"; done

EXPOSE 8080
CMD ["nanobot", "serve", "--config", "config/nanobot.yaml", "--host", "0.0.0.0", "--port", "8080"]
