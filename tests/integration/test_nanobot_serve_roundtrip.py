"""启 nanobot serve 子进程，发 /v1/chat/completions，断言 metadata.executed_tools 存在。

跳过条件：
  - 没有 OPENAI_API_KEY
  - nanobot CLI 不可用
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
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

    # 先套 patch
    subprocess.run(["bash", str(ROOT / "scripts/apply_patches.sh")], check=True)

    proc = subprocess.Popen(
        [nanobot_bin, "serve",
         "--config", str(ROOT / "config/nanobot.yaml"),
         "--host", "127.0.0.1", "--port", "18080"],
        cwd=str(ROOT),
        env={**os.environ},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    # 等就绪
    started = False
    for _ in range(60):  # 最多 60 秒
        try:
            r = httpx.get("http://127.0.0.1:18080/health", timeout=1.0)
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


def test_health(nanobot_process) -> None:
    r = httpx.get("http://127.0.0.1:18080/health")
    assert r.status_code == 200


def test_chat_completions_has_executed_tools_metadata(nanobot_process) -> None:
    """发 chat，断言响应含 metadata.executed_tools（patch 正常）。"""
    r = httpx.post(
        "http://127.0.0.1:18080/v1/chat/completions",
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "计算 (2+3)*4 是多少"}],
            "stream": False,
        },
        timeout=60.0,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "metadata" in data, f"patch 未生效？响应：{data}"
    assert "executed_tools" in data["metadata"]
    # 若 AgentLoop 真调了 calculator，executed_tools 应含一项 name=calculator
    names = [t.get("name") for t in data["metadata"]["executed_tools"]]
    # M1 接受空列表（LLM 可能选择不调用），但字段必须存在
    print(f"executed_tools names: {names}")
