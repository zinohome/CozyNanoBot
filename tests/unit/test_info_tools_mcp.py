"""Unit tests for the info_tools MCP server (cozy_mcp_tools.info_tools.__main__)."""

from __future__ import annotations

import math
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from cozy_mcp_tools.info_tools.__main__ import (
    _convert_temp,
    current_time,
    unit_convert,
)


# ---------------------------------------------------------------------------
# current_time
# ---------------------------------------------------------------------------

def test_current_time_default_timezone() -> None:
    result = current_time()
    assert result["timezone"] == "Asia/Shanghai"
    assert "datetime" in result
    assert "weekday" in result
    assert "unix" in result
    assert "error" not in result
    # weekday must be one of the Chinese labels
    assert result["weekday"] in {"周一", "周二", "周三", "周四", "周五", "周六", "周日"}


def test_current_time_explicit_iana() -> None:
    result = current_time("America/New_York")
    assert result["timezone"] == "America/New_York"
    assert "error" not in result


def test_current_time_alias_beijing() -> None:
    result = current_time("beijing")
    assert result["timezone"] == "Asia/Shanghai"
    assert "error" not in result


def test_current_time_alias_tokyo() -> None:
    result = current_time("tokyo")
    assert result["timezone"] == "Asia/Tokyo"
    assert "error" not in result


def test_current_time_alias_new_york() -> None:
    # alias key is "new york" (with space)
    result = current_time("new york")
    assert result["timezone"] == "America/New_York"
    assert "error" not in result


def test_current_time_alias_nyc() -> None:
    result = current_time("nyc")
    assert result["timezone"] == "America/New_York"
    assert "error" not in result


def test_current_time_alias_utc() -> None:
    result = current_time("utc")
    assert result["timezone"] == "UTC"
    assert "error" not in result


def test_current_time_invalid_timezone() -> None:
    result = current_time("Not/AReal_Zone")
    assert "error" in result
    assert "未知时区" in result["error"]


def test_current_time_unix_is_reasonable() -> None:
    """unix timestamp should be within a few seconds of now."""
    import time as _time
    result = current_time()
    assert abs(result["unix"] - int(_time.time())) <= 5


def test_current_time_datetime_format() -> None:
    """datetime field must be ISO 8601 parseable."""
    result = current_time("Asia/Shanghai")
    dt = datetime.fromisoformat(result["datetime"])
    assert dt.tzinfo is not None


def test_current_time_frozen(monkeypatch: pytest.MonkeyPatch) -> None:
    """Freeze datetime to verify weekday computation."""
    # 2024-01-01 is a Monday (weekday index 0 → 周一)
    fixed_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    with patch(
        "cozy_mcp_tools.info_tools.__main__.datetime"
    ) as mock_dt:
        mock_dt.now.return_value = fixed_dt
        result = current_time("Asia/Shanghai")

    assert result["weekday"] == "周一"


# ---------------------------------------------------------------------------
# _convert_temp
# ---------------------------------------------------------------------------

def test_convert_temp_c_to_f_zero() -> None:
    assert _convert_temp(0, "c", "f") == pytest.approx(32.0)


def test_convert_temp_c_to_f_hundred() -> None:
    assert _convert_temp(100, "c", "f") == pytest.approx(212.0)


def test_convert_temp_f_to_c_boiling() -> None:
    assert _convert_temp(212, "f", "c") == pytest.approx(100.0)


def test_convert_temp_f_to_c_freezing() -> None:
    assert _convert_temp(32, "f", "c") == pytest.approx(0.0)


def test_convert_temp_c_to_k() -> None:
    assert _convert_temp(0, "c", "k") == pytest.approx(273.15)


def test_convert_temp_k_to_c() -> None:
    assert _convert_temp(273.15, "k", "c") == pytest.approx(0.0)


def test_convert_temp_f_to_k() -> None:
    # 32°F = 0°C = 273.15 K
    assert _convert_temp(32, "f", "k") == pytest.approx(273.15)


def test_convert_temp_same_unit() -> None:
    assert _convert_temp(25, "c", "c") == pytest.approx(25.0)


def test_convert_temp_celsius_aliases() -> None:
    """Test 'celsius' long-form alias."""
    assert _convert_temp(0, "celsius", "fahrenheit") == pytest.approx(32.0)


def test_convert_temp_unknown_src_raises() -> None:
    with pytest.raises(ValueError, match="unknown temperature unit"):
        _convert_temp(100, "x", "c")


def test_convert_temp_unknown_dst_raises() -> None:
    with pytest.raises(ValueError, match="unknown temperature unit"):
        _convert_temp(100, "c", "z")


# ---------------------------------------------------------------------------
# unit_convert — temperature
# ---------------------------------------------------------------------------

def test_unit_convert_temperature_c_to_f() -> None:
    result = unit_convert(0, "C", "F")
    assert result["result"] == pytest.approx(32.0)
    assert result["category"] == "temperature"
    assert result["value"] == 0
    assert result["from_unit"] == "C"
    assert result["to_unit"] == "F"


def test_unit_convert_temperature_f_to_c() -> None:
    result = unit_convert(212, "F", "C")
    assert result["result"] == pytest.approx(100.0)
    assert result["category"] == "temperature"


# ---------------------------------------------------------------------------
# unit_convert — length
# ---------------------------------------------------------------------------

def test_unit_convert_length_m_to_ft() -> None:
    # 1 m = 1 / 0.3048 ft ≈ 3.28084 ft
    result = unit_convert(1, "m", "ft")
    assert result["result"] == pytest.approx(1 / 0.3048, rel=1e-4)
    assert result["category"] == "length"


def test_unit_convert_length_km_to_mi() -> None:
    # 1 km = 1000 m / 1609.344 m/mi ≈ 0.621371 mi
    result = unit_convert(1, "km", "mi")
    assert result["result"] == pytest.approx(1000 / 1609.344, rel=1e-4)
    assert result["category"] == "length"


def test_unit_convert_length_ft_to_m() -> None:
    result = unit_convert(1, "ft", "m")
    assert result["result"] == pytest.approx(0.3048, rel=1e-4)
    assert result["category"] == "length"


def test_unit_convert_length_cm_to_mm() -> None:
    result = unit_convert(5, "cm", "mm")
    assert result["result"] == pytest.approx(50.0, rel=1e-4)


# ---------------------------------------------------------------------------
# unit_convert — weight
# ---------------------------------------------------------------------------

def test_unit_convert_weight_kg_to_lb() -> None:
    # 1 kg = 1000 g / 453.592 g/lb ≈ 2.20462 lb
    result = unit_convert(1, "kg", "lb")
    assert result["result"] == pytest.approx(1000 / 453.592, rel=1e-4)
    assert result["category"] == "weight"


def test_unit_convert_weight_g_to_oz() -> None:
    # 1 g = 1 g / 28.3495 g/oz ≈ 0.035274 oz
    result = unit_convert(1, "g", "oz")
    assert result["result"] == pytest.approx(1 / 28.3495, rel=1e-4)
    assert result["category"] == "weight"


def test_unit_convert_weight_lb_to_kg() -> None:
    result = unit_convert(1, "lb", "kg")
    assert result["result"] == pytest.approx(453.592 / 1000, rel=1e-4)


def test_unit_convert_weight_ton_to_kg() -> None:
    # 1 ton = 1_000_000 g / 1000 g/kg = 1000 kg
    result = unit_convert(1, "ton", "kg")
    assert result["result"] == pytest.approx(1000.0, rel=1e-4)


# ---------------------------------------------------------------------------
# unit_convert — same unit (identity)
# ---------------------------------------------------------------------------

def test_unit_convert_same_unit_length() -> None:
    result = unit_convert(42, "m", "m")
    assert result["result"] == pytest.approx(42.0)
    assert result["category"] == "length"


def test_unit_convert_same_unit_weight() -> None:
    result = unit_convert(5, "kg", "kg")
    assert result["result"] == pytest.approx(5.0)
    assert result["category"] == "weight"


def test_unit_convert_same_unit_temperature() -> None:
    result = unit_convert(37, "c", "c")
    assert result["result"] == pytest.approx(37.0)
    assert result["category"] == "temperature"


# ---------------------------------------------------------------------------
# unit_convert — unsupported / cross-category
# ---------------------------------------------------------------------------

def test_unit_convert_unsupported_pair() -> None:
    result = unit_convert(1, "kg", "m")
    assert "error" in result


def test_unit_convert_unknown_unit() -> None:
    result = unit_convert(1, "parsec", "km")
    assert "error" in result


def test_unit_convert_cross_category_weight_length() -> None:
    result = unit_convert(1, "lb", "ft")
    assert "error" in result
