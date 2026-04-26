"""Weather MCP tool unit tests — fully mocked, no real HTTP calls."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from cozy_mcp_tools.weather.__main__ import _translate_condition, weather


def _make_wttr_response(
    temp_c: int = 22,
    feels_like_c: int = 20,
    humidity: int = 65,
    wind_speed: str = "15",
    wind_dir: str = "NE",
    condition_en: str = "Clear",
) -> dict:
    return {
        "current_condition": [
            {
                "temp_C": str(temp_c),
                "FeelsLikeC": str(feels_like_c),
                "humidity": str(humidity),
                "windspeedKmph": wind_speed,
                "winddir16Point": wind_dir,
                "weatherDesc": [{"value": condition_en}],
            }
        ]
    }


def _mock_http_response(json_data: dict, status_code: int = 200) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json = MagicMock(return_value=json_data)
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


# ---------------------------------------------------------------------------
# Test 1: normal city returns all expected fields correctly
# ---------------------------------------------------------------------------

def test_normal_city_returns_all_fields() -> None:
    json_data = _make_wttr_response(
        temp_c=25,
        feels_like_c=23,
        humidity=70,
        wind_speed="20",
        wind_dir="SW",
        condition_en="Sunny",
    )
    with patch("cozy_mcp_tools.weather.__main__.httpx.get", return_value=_mock_http_response(json_data)):
        result = weather("上海")

    assert result["city"] == "上海"
    assert result["temperature"] == 25
    assert result["feels_like"] == 23
    assert result["humidity"] == 70
    assert result["wind"] == "20 km/h SW"
    assert result["condition"] == "晴"  # "Sunny" → "晴"
    assert result["source"] == "wttr.in"
    assert "error" not in result


# ---------------------------------------------------------------------------
# Test 2: _translate_condition maps known English conditions to Chinese
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("en,expected_cn", [
    ("Clear", "晴"),
    ("Sunny", "晴"),
    ("Partly cloudy", "多云"),
    ("Cloudy", "多云"),
    ("Overcast", "阴"),
    ("Mist", "薄雾"),
    ("Fog", "雾"),
    ("Patchy rain possible", "可能有阵雨"),
    ("Light rain", "小雨"),
    ("Moderate rain", "中雨"),
    ("Heavy rain", "大雨"),
    ("Light snow", "小雪"),
    ("Moderate snow", "中雪"),
    ("Heavy snow", "大雪"),
    ("Thunderstorm", "雷暴"),
    ("Patchy rain nearby", "附近有阵雨"),
])
def test_translate_condition_known_values(en: str, expected_cn: str) -> None:
    assert _translate_condition(en) == expected_cn


# ---------------------------------------------------------------------------
# Test 3: _translate_condition returns original string for unknown conditions
# ---------------------------------------------------------------------------

def test_translate_condition_unknown_returns_original() -> None:
    unknown = "Hailing Frogs"
    assert _translate_condition(unknown) == unknown


# ---------------------------------------------------------------------------
# Test 4: TimeoutException returns error dict
# ---------------------------------------------------------------------------

def test_timeout_returns_error_dict() -> None:
    with patch(
        "cozy_mcp_tools.weather.__main__.httpx.get",
        side_effect=httpx.TimeoutException("timed out"),
    ):
        result = weather("Tokyo")

    assert result["city"] == "Tokyo"
    assert "error" in result
    assert "超时" in result["error"]
    assert "temperature" not in result


# ---------------------------------------------------------------------------
# Test 5: HTTP 404 error returns error dict with status code
# ---------------------------------------------------------------------------

def test_http_404_returns_error_dict() -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    http_error = httpx.HTTPStatusError(
        "Not Found",
        request=MagicMock(),
        response=mock_resp,
    )
    with patch(
        "cozy_mcp_tools.weather.__main__.httpx.get",
        side_effect=http_error,
    ):
        result = weather("火星")

    assert result["city"] == "火星"
    assert "error" in result
    assert "404" in result["error"]
    assert "temperature" not in result


# ---------------------------------------------------------------------------
# Test 6: generic exception returns error dict
# ---------------------------------------------------------------------------

def test_generic_exception_returns_error_dict() -> None:
    with patch(
        "cozy_mcp_tools.weather.__main__.httpx.get",
        side_effect=ValueError("unexpected json structure"),
    ):
        result = weather("北京")

    assert result["city"] == "北京"
    assert "error" in result
    assert "ValueError" in result["error"]
    assert "temperature" not in result
