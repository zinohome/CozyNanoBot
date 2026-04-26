"""Unit tests for the translate MCP server (cozy_mcp_tools.translate.__main__)."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from unittest.mock import MagicMock, patch

import httpx
import pytest

from cozy_mcp_tools.translate.__main__ import (
    _build_auth_header,
    _sign,
    translate,
)


# ---------------------------------------------------------------------------
# _sign helpers
# ---------------------------------------------------------------------------

def test_sign_produces_correct_hmac_sha256() -> None:
    key = b"secret"
    msg = "hello"
    expected = hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()
    result = _sign(key, msg)
    assert result == expected


def test_sign_different_keys_produce_different_results() -> None:
    a = _sign(b"key_a", "message")
    b = _sign(b"key_b", "message")
    assert a != b


def test_sign_different_msgs_produce_different_results() -> None:
    a = _sign(b"key", "msg_a")
    b = _sign(b"key", "msg_b")
    assert a != b


# ---------------------------------------------------------------------------
# _build_auth_header
# ---------------------------------------------------------------------------

def test_build_auth_header_format() -> None:
    secret_id = "AKIDtest"
    secret_key = "secretkey"
    payload = '{"SourceText":"hello","Source":"auto","Target":"zh","ProjectId":0}'
    timestamp = 1700000000

    auth, date = _build_auth_header(secret_id, secret_key, payload, timestamp)

    # Authorization string format check
    assert auth.startswith("TC3-HMAC-SHA256 ")
    assert f"Credential={secret_id}/" in auth
    assert "SignedHeaders=content-type;host;x-tc-action" in auth
    assert "Signature=" in auth

    # date should match the timestamp
    expected_date = time.strftime("%Y-%m-%d", time.gmtime(timestamp))
    assert date == expected_date


def test_build_auth_header_deterministic() -> None:
    """Same inputs produce the same output (no randomness)."""
    args = ("AKIDtest", "secretkey", '{"foo":"bar"}', 1700000000)
    auth1, date1 = _build_auth_header(*args)
    auth2, date2 = _build_auth_header(*args)
    assert auth1 == auth2
    assert date1 == date2


def test_build_auth_header_different_payloads_differ() -> None:
    auth1, _ = _build_auth_header("id", "key", '{"a":1}', 1700000000)
    auth2, _ = _build_auth_header("id", "key", '{"a":2}', 1700000000)
    # Different payloads → different signatures
    sig1 = auth1.split("Signature=")[1]
    sig2 = auth2.split("Signature=")[1]
    assert sig1 != sig2


# ---------------------------------------------------------------------------
# translate — success path
# ---------------------------------------------------------------------------

_GOOD_ENV = {"TENCENT_SECRET_ID": "AKIDtest", "TENCENT_SECRET_KEY": "secretkey"}


def _mock_httpx_post(json_response: dict):
    """Return a context-manager-compatible mock for httpx.post."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = json_response
    return mock_resp


def test_translate_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TENCENT_SECRET_ID", "AKIDtest")
    monkeypatch.setenv("TENCENT_SECRET_KEY", "secretkey")

    api_response = {
        "Response": {
            "TargetText": "你好世界",
            "Source": "en",
            "Target": "zh",
            "RequestId": "abc",
        }
    }
    with patch("cozy_mcp_tools.translate.__main__.httpx.post") as mock_post:
        mock_post.return_value = _mock_httpx_post(api_response)
        result = translate("Hello world", "zh", "auto")

    assert result["translated_text"] == "你好世界"
    assert result["source_lang"] == "en"
    assert result["target_lang"] == "zh"
    assert result["source_text"] == "Hello world"
    assert result["source"] == "tencent_tmt"
    assert "error" not in result


def test_translate_auto_source_detection(monkeypatch: pytest.MonkeyPatch) -> None:
    """source_lang defaults to 'auto' and resolved_src comes from API response."""
    monkeypatch.setenv("TENCENT_SECRET_ID", "AKIDtest")
    monkeypatch.setenv("TENCENT_SECRET_KEY", "secretkey")

    api_response = {
        "Response": {
            "TargetText": "Hola",
            "Source": "zh",  # API resolved the auto source
            "Target": "es",
            "RequestId": "xyz",
        }
    }
    with patch("cozy_mcp_tools.translate.__main__.httpx.post") as mock_post:
        mock_post.return_value = _mock_httpx_post(api_response)
        result = translate("你好", "es")  # source_lang omitted → "auto"

    assert result["source_lang"] == "zh"
    assert result["target_lang"] == "es"
    assert result["translated_text"] == "Hola"


# ---------------------------------------------------------------------------
# translate — validation errors (no HTTP call needed)
# ---------------------------------------------------------------------------

def test_translate_unsupported_target_lang() -> None:
    result = translate("hello", "xx")
    assert "error" in result
    assert "target_lang" in result["error"]


def test_translate_target_lang_auto_is_rejected() -> None:
    """'auto' is in _SUPPORTED_LANGS but not allowed as target."""
    result = translate("hello", "auto")
    assert "error" in result


def test_translate_empty_text(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TENCENT_SECRET_ID", "AKIDtest")
    monkeypatch.setenv("TENCENT_SECRET_KEY", "secretkey")
    result = translate("   ", "zh")
    assert "error" in result
    assert result["error"] == "text 为空"


def test_translate_empty_string(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TENCENT_SECRET_ID", "AKIDtest")
    monkeypatch.setenv("TENCENT_SECRET_KEY", "secretkey")
    result = translate("", "zh")
    assert "error" in result


def test_translate_missing_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TENCENT_SECRET_ID", raising=False)
    monkeypatch.delenv("TENCENT_SECRET_KEY", raising=False)
    result = translate("hello", "zh")
    assert "error" in result
    assert "not configured" in result["error"]


def test_translate_missing_secret_id_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TENCENT_SECRET_ID", raising=False)
    monkeypatch.setenv("TENCENT_SECRET_KEY", "secretkey")
    result = translate("hello", "zh")
    assert "error" in result
    assert "not configured" in result["error"]


def test_translate_missing_secret_key_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TENCENT_SECRET_ID", "AKIDtest")
    monkeypatch.delenv("TENCENT_SECRET_KEY", raising=False)
    result = translate("hello", "zh")
    assert "error" in result
    assert "not configured" in result["error"]


# ---------------------------------------------------------------------------
# translate — API-level error response
# ---------------------------------------------------------------------------

def test_translate_api_error_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TENCENT_SECRET_ID", "AKIDtest")
    monkeypatch.setenv("TENCENT_SECRET_KEY", "secretkey")

    api_response = {
        "Response": {
            "Error": {
                "Code": "AuthFailure.SignatureFailure",
                "Message": "The provided credentials could not be validated.",
            },
            "RequestId": "err123",
        }
    }
    with patch("cozy_mcp_tools.translate.__main__.httpx.post") as mock_post:
        mock_post.return_value = _mock_httpx_post(api_response)
        result = translate("hello", "zh")

    assert "error" in result
    assert "TMT API 错误" in result["error"]
    assert "AuthFailure.SignatureFailure" in result["error"]


# ---------------------------------------------------------------------------
# translate — network / HTTP exceptions
# ---------------------------------------------------------------------------

def test_translate_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TENCENT_SECRET_ID", "AKIDtest")
    monkeypatch.setenv("TENCENT_SECRET_KEY", "secretkey")

    with patch("cozy_mcp_tools.translate.__main__.httpx.post") as mock_post:
        mock_post.side_effect = httpx.TimeoutException("timed out")
        result = translate("hello", "zh")

    assert "error" in result
    assert "超时" in result["error"]


def test_translate_http_status_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TENCENT_SECRET_ID", "AKIDtest")
    monkeypatch.setenv("TENCENT_SECRET_KEY", "secretkey")

    mock_response = MagicMock()
    mock_response.status_code = 503
    http_error = httpx.HTTPStatusError(
        "Service Unavailable",
        request=MagicMock(),
        response=mock_response,
    )
    with patch("cozy_mcp_tools.translate.__main__.httpx.post") as mock_post:
        mock_post.side_effect = http_error
        result = translate("hello", "zh")

    assert "error" in result
    assert "503" in result["error"]


def test_translate_generic_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TENCENT_SECRET_ID", "AKIDtest")
    monkeypatch.setenv("TENCENT_SECRET_KEY", "secretkey")

    with patch("cozy_mcp_tools.translate.__main__.httpx.post") as mock_post:
        mock_post.side_effect = RuntimeError("unexpected")
        result = translate("hello", "zh")

    assert "error" in result
    assert "RuntimeError" in result["error"]
