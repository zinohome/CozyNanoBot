# CozyNanoBot

**CozyEngineV2 Brain 项目的小脑服务**：[HKUDS/nanobot](https://github.com/HKUDS/nanobot) 之上的 Cozy 层，负责：
- 锁定 upstream 版本 + 叠加 Cozy 定制 patch
- 把"自定义工具"以独立 MCP server 进程暴露给 nanobot
- 打包 Dockerfile / 配置 / 启动脚本一站式部署

## 快速开始

```bash
git clone <this-repo> CozyNanoBot
cd CozyNanoBot
git submodule update --init --recursive

python3.11 -m venv .venv
source .venv/bin/activate
pip install -e upstream/nanobot
pip install -e .

# 1) 套 patch（executed_tools metadata）
bash scripts/apply_patches.sh

# 2) 填 OPENAI_API_KEY 到环境变量
export OPENAI_API_KEY=sk-...

# 3) 启动（nanobot serve 本身会 spawn MCP server 子进程）
bash scripts/start.sh
```

## 架构

```
  +------+  HTTP /v1/chat/completions
  |Brain | --------------> [ nanobot serve (aiohttp :8080) ]
  +------+                         |
                                   |  stdio (spawned subprocess)
                                   v
                         +-------- MCP servers --------+
                         |  weather  search  calculator |
                         +------------------------------+
```

- `nanobot serve` 作为 OpenAI 兼容 API 门面
- 我们的工具是独立 MCP stdio server（官方协议），nanobot 通过 config 的 `mcp_servers` 连上
- `metadata.executed_tools` 由我们的 patch 在响应里追加

## 升级 upstream

```bash
cd upstream/nanobot
git fetch && git checkout <new-sha>
cd ../..
bash scripts/apply_patches.sh   # 若失败则手动 rebase patches/
git add upstream/nanobot
git commit -m "chore: bump upstream to <new-sha>"
```

## 关联项目

- [CozyEngineV2](https://github.com/zinohome/CozyEngineV2) — Brain 消费方
- [HKUDS/nanobot](https://github.com/HKUDS/nanobot) — upstream
- [Model Context Protocol](https://modelcontextprotocol.io/) — MCP 规范
