"""Allowlist enforcement test — patch 0002.

启 nanobot serve，发一个明显需要 search 的问题，但 `allowed_tools=["calculator"]`。
断言：响应的 metadata.executed_tools 里不包含 search（因为 patch 在
runner._run_tool 入口短路了非白名单工具），并且（若模型确实尝试了 search）
应该有 `status=denied` 的 tool_event 被捕获。因为 nanobot 目前没有把
tool_events 暴露到 /v1/chat/completions 响应，我们只能保底断言 executed_tools
的 name 集合完全落在 allowed_tools 内。

跳过条件：
  - 没有 OPENAI_API_KEY
  - nanobot CLI 不可用
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

import httpx
import pytest

pytestmark = pytest.mark.integration

ROOT = Path(__file__).parent.parent.parent


@pytest.fixture(scope="module")
def nanobot_process():
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    nanobot_bin = shutil.which("nanobot") or str(ROOT / ".venv/bin/nanobot")
    if not Path(nanobot_bin).exists():
        pytest.skip(f"nanobot CLI not found at {nanobot_bin}")

    # 套 patch（0001 + 0002）
    subprocess.run(["bash", str(ROOT / "scripts/apply_patches.sh")], check=True)

    proc = subprocess.Popen(
        [nanobot_bin, "serve",
         "--config", str(ROOT / "config/nanobot.yaml"),
         "--host", "127.0.0.1", "--port", "18081"],
        cwd=str(ROOT),
        env={**os.environ},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    started = False
    for _ in range(60):
        try:
            r = httpx.get("http://127.0.0.1:18081/health", timeout=1.0)
            if r.status_code == 200:
                started = True
                break
        except Exception:
            time.sleep(1)
    if not started:
        proc.kill()
        stdout = proc.stdout.read().decode() if proc.stdout else ""
        pytest.fail(f"nanobot serve did not start in 60s:\n{stdout[:2000]}")

    yield proc

    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


def test_nanobot_rejects_non_whitelisted_tool(nanobot_process) -> None:
    """allowed_tools=['calculator']，问明显要 search 的问题 → 不应执行 search。"""
    r = httpx.post(
        "http://127.0.0.1:18081/v1/chat/completions",
        json={
            "model": "gpt-4o-mini",
            "messages": [{
                "role": "user",
                "content": "用 web_search 搜一下 Anthropic 最新的 Claude 模型版本是哪个",
            }],
            "allowed_tools": ["calculator"],
            "session_id": "test-allowlist-block",
            "stream": False,
        },
        timeout=90.0,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    executed = data.get("metadata", {}).get("executed_tools", [])
    names = {t.get("name") for t in executed}
    # 所有执行过的工具必须落在 allowlist 内
    assert names.issubset({"calculator"}), (
        f"allowlist breached: executed={names}, allowed=['calculator']"
    )


def test_nanobot_empty_allowlist_blocks_all_tools(nanobot_process) -> None:
    """allowed_tools=[] → 模型若尝试任何工具都应被 deny → executed_tools 为空。"""
    r = httpx.post(
        "http://127.0.0.1:18081/v1/chat/completions",
        json={
            "model": "gpt-4o-mini",
            "messages": [{
                "role": "user",
                "content": "计算 (2+3)*4 是多少",
            }],
            "allowed_tools": [],
            "session_id": "test-allowlist-empty",
            "stream": False,
        },
        timeout=90.0,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    executed = data.get("metadata", {}).get("executed_tools", [])
    assert executed == [], (
        f"empty allowlist should block all tools, but got executed={executed}"
    )


def test_nanobot_no_allowlist_preserves_legacy_behavior(nanobot_process) -> None:
    """不传 allowed_tools → 兼容旧行为（不限制）。"""
    r = httpx.post(
        "http://127.0.0.1:18081/v1/chat/completions",
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "计算 1+1 是多少"}],
            "session_id": "test-allowlist-absent",
            "stream": False,
        },
        timeout=90.0,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    # metadata 字段必须存在（0001），executed_tools 可能含 calculator 也可能为空
    assert "metadata" in data
    assert "executed_tools" in data["metadata"]
