"""Translate MCP server — 腾讯云机器翻译 TMT（TextTranslate）。

使用 httpx + 手写 TC3-HMAC-SHA256 签名（不引入 tencentcloud-sdk-python-tmt，避免体积膨胀）。
Env:
  TENCENT_SECRET_ID
  TENCENT_SECRET_KEY

签名算法参考官方文档：
  https://cloud.tencent.com/document/api/551/30636
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

from cozy_mcp_tools._common import emit_log, setup_logging

logger = setup_logging("translate")
mcp = FastMCP("cozy-translate")

_HOST = "tmt.tencentcloudapi.com"
_SERVICE = "tmt"
_VERSION = "2018-03-21"
_ACTION = "TextTranslate"
_REGION = "ap-beijing"
_ALGORITHM = "TC3-HMAC-SHA256"
_TIMEOUT = 10.0

_SUPPORTED_LANGS = {
    "auto", "zh", "en", "ja", "ko", "fr", "de", "es", "it", "ru", "pt", "th", "vi",
}


def _sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _build_auth_header(
    secret_id: str,
    secret_key: str,
    payload: str,
    timestamp: int,
) -> tuple[str, str]:
    """返回 (authorization, date)。"""
    date = time.strftime("%Y-%m-%d", time.gmtime(timestamp))

    # 1) CanonicalRequest
    http_method = "POST"
    canonical_uri = "/"
    canonical_query = ""
    canonical_headers = (
        f"content-type:application/json; charset=utf-8\n"
        f"host:{_HOST}\n"
        f"x-tc-action:{_ACTION.lower()}\n"
    )
    signed_headers = "content-type;host;x-tc-action"
    hashed_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    canonical_request = (
        f"{http_method}\n{canonical_uri}\n{canonical_query}\n"
        f"{canonical_headers}\n{signed_headers}\n{hashed_payload}"
    )

    # 2) StringToSign
    credential_scope = f"{date}/{_SERVICE}/tc3_request"
    hashed_canonical_request = hashlib.sha256(
        canonical_request.encode("utf-8")
    ).hexdigest()
    string_to_sign = (
        f"{_ALGORITHM}\n{timestamp}\n{credential_scope}\n{hashed_canonical_request}"
    )

    # 3) Signature
    secret_date = _sign(f"TC3{secret_key}".encode("utf-8"), date)
    secret_service = _sign(secret_date, _SERVICE)
    secret_signing = _sign(secret_service, "tc3_request")
    signature = hmac.new(
        secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    authorization = (
        f"{_ALGORITHM} "
        f"Credential={secret_id}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )
    return authorization, date


@mcp.tool()
def translate(
    text: str,
    target_lang: str,
    source_lang: str = "auto",
) -> dict[str, Any]:
    """翻译文本（腾讯云机器翻译 TMT）。**只要用户显式说"翻译/译/translate"+ 内容或目标语言**，就调这个工具。

    触发示例：
    - "翻译 'hello world' 到中文"
    - "把这句话翻译成日文"
    - "将 I love you 译成法语"
    - "translate 你好 to English"

    不触发：一般闲聊里出现的外语（没有"翻译"意图）。

    支持语言 (target_lang)：zh, en, ja, ko, fr, de, es, it, ru, pt, th, vi
    source_lang 默认 auto（自动识别）。

    Args:
        text: 待翻译文本
        target_lang: 目标语言代码
        source_lang: 源语言代码，默认 "auto"

    Returns:
        成功: {source_lang, target_lang, source_text, translated_text, source: "tencent_tmt"}
        失败: {error}
    """
    if target_lang not in _SUPPORTED_LANGS or target_lang == "auto":
        return {"error": f"不支持的 target_lang: {target_lang}"}
    if source_lang not in _SUPPORTED_LANGS:
        return {"error": f"不支持的 source_lang: {source_lang}"}
    if not text or not text.strip():
        return {"error": "text 为空"}

    secret_id = os.getenv("TENCENT_SECRET_ID", "").strip()
    secret_key = os.getenv("TENCENT_SECRET_KEY", "").strip()
    if not secret_id or not secret_key:
        return {"error": "TENCENT_SECRET_ID/KEY not configured"}

    logger.info("translate: %s -> %s (len=%d)", source_lang, target_lang, len(text))
    emit_log(tool="translate", action="start", source_lang=source_lang, target_lang=target_lang)
    _start = time.monotonic()

    payload_dict = {
        "SourceText": text,
        "Source": source_lang,
        "Target": target_lang,
        "ProjectId": 0,
    }
    payload = json.dumps(payload_dict, ensure_ascii=False, separators=(",", ":"))
    timestamp = int(time.time())

    try:
        authorization, _date = _build_auth_header(
            secret_id, secret_key, payload, timestamp
        )
    except Exception as e:
        logger.exception("sign failed")
        emit_log(
            tool="translate", action="end",
            duration_ms=round((time.monotonic() - _start) * 1000, 2),
            status="error", error="sign_failed",
            source_lang=source_lang, target_lang=target_lang,
        )
        return {"error": f"签名生成失败: {type(e).__name__}"}

    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json; charset=utf-8",
        "Host": _HOST,
        "X-TC-Action": _ACTION,
        "X-TC-Timestamp": str(timestamp),
        "X-TC-Version": _VERSION,
        "X-TC-Region": _REGION,
    }

    try:
        resp = httpx.post(
            f"https://{_HOST}/",
            content=payload.encode("utf-8"),
            headers=headers,
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        response = data.get("Response", {})
        if "Error" in response:
            err = response["Error"]
            emit_log(
                tool="translate", action="end",
                duration_ms=round((time.monotonic() - _start) * 1000, 2),
                status="error", error=f"api_{err.get('Code')}",
                source_lang=source_lang, target_lang=target_lang,
            )
            return {
                "error": f"TMT API 错误: {err.get('Code')} - {err.get('Message')}"
            }
        translated = response.get("TargetText", "")
        resolved_src = response.get("Source", source_lang)
        emit_log(
            tool="translate", action="end",
            duration_ms=round((time.monotonic() - _start) * 1000, 2),
            status="ok", source_lang=source_lang, target_lang=target_lang,
        )
        return {
            "source_lang": resolved_src,
            "target_lang": target_lang,
            "source_text": text,
            "translated_text": translated,
            "source": "tencent_tmt",
        }
    except httpx.TimeoutException:
        logger.warning("translate timeout")
        emit_log(
            tool="translate", action="end",
            duration_ms=round((time.monotonic() - _start) * 1000, 2),
            status="error", error="timeout",
            source_lang=source_lang, target_lang=target_lang,
        )
        return {"error": "翻译超时（10s），请稍后再试"}
    except httpx.HTTPStatusError as e:
        logger.warning("translate http error %s", e.response.status_code)
        emit_log(
            tool="translate", action="end",
            duration_ms=round((time.monotonic() - _start) * 1000, 2),
            status="error", error=f"http_{e.response.status_code}",
            source_lang=source_lang, target_lang=target_lang,
        )
        return {"error": f"翻译服务异常 (HTTP {e.response.status_code})"}
    except Exception as e:
        logger.exception("translate unexpected error")
        emit_log(
            tool="translate", action="end",
            duration_ms=round((time.monotonic() - _start) * 1000, 2),
            status="error", error=f"{type(e).__name__}",
            source_lang=source_lang, target_lang=target_lang,
        )
        return {"error": f"翻译失败: {type(e).__name__}"}


if __name__ == "__main__":
    mcp.run(transport="stdio")
