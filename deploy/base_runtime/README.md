# CozyNanoBot Base Runtime (1Panel 风格)

本目录提供 CozyNanoBot 的 1Panel 部署编排文件，与 CozyMemory 的 `base_runtime/` 布局保持一致。

## 文件

| 文件 | 作用 |
|---|---|
| `docker-compose.1panel.yml` | 1Panel 专用 Compose（网络 `1panel-network` 为 external） |
| `Caddyfile` | 反向代理（`:8080 → cozy_nanobot:8080`） |
| `build.sh` | 构建 `cozy-nanobot:latest` 镜像 |
| `.env.example` | 模板；部署前复制为 `.env` 并填充 key |

## 快速部署

```bash
# 1) 准备外部网络（若尚未存在）
docker network create 1panel-network || true

# 2) 准备 .env
cp .env.example .env
vim .env   # 填入 OPENAI_API_KEY（或其他 provider key）

# 3) 准备持久化目录
sudo mkdir -p /data/CozyNanoBot/workspace /data/CozyNanoBot/caddy/{data,config}

# 4) 构建镜像（自动初始化 submodule + 套 patch）
bash build.sh

# 5) 校验 Compose 语法
docker compose -f docker-compose.1panel.yml config

# 6) 启动
docker compose -f docker-compose.1panel.yml up -d

# 7) 检查健康状态
docker ps --filter name=cozy_nanobot
curl -fsS http://127.0.0.1:8080/health
```

## 配置说明

### 数据持久化

- `/data/CozyNanoBot/workspace/` → 容器内 `/workspace`，nanobot agent 工作目录。
- `/data/CozyNanoBot/caddy/{data,config}/` → Caddy 自身状态（证书等）。

### 覆盖 `nanobot.yaml`

镜像已内置 `/app/config/nanobot.yaml`。如需线上覆盖，在 Compose 里取消这一行注释：

```yaml
# - ./nanobot.yaml:/app/config/nanobot.yaml:ro
```

然后在当前目录放一份 `nanobot.yaml`。

### LLM Provider

默认只要求 `OPENAI_API_KEY`。若需接其他 provider，参考 upstream nanobot 文档扩展 `config/nanobot.yaml` 的 `providers:` 段。

## Troubleshooting

- **`docker build` 失败 / submodule 缺失**：确保在仓库根路径执行过 `git submodule update --init --recursive`（`build.sh` 会自动做，但若无网络会失败）。
- **`git network 1panel-network not found`**：先执行 `docker network create 1panel-network`。
- **`/health` 不通**：nanobot serve 启动约需 5–15s，等 `start_period`（30s）后再看。
