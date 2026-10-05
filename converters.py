"""Base (radix) conversion and unit conversion utilities.

All conversion logic runs on the backend so the frontend never computes
results directly.
"""

from __future__ import annotations

from dataclasses import dataclass


class ConvertError(Exception):
    """Raised when a conversion cannot be performed."""


# --------------------------------------------------------------------------- #
# Base conversion
# --------------------------------------------------------------------------- #

VALID_BASES = {2, 8, 10, 16}
BASE_PREFIX = {2: "0b", 8: "0o", 10: "", 16: "0x"}


def convert_base(value: str, from_base: int, to_base: int) -> str:
    """Convert an integer value string from one base to another.

    Args:
        value: The number as a string (e.g. ``"FF"`` for hex).
        from_base: Source base (2, 8, 10, or 16).
        to_base: Target base (2, 8, 10, or 16).

    Returns:
        The converted value as a string with the appropriate prefix
        (e.g. ``"0xFF"``).
    """
    if from_base not in VALID_BASES or to_base not in VALID_BASES:
        raise ConvertError(f"不支持的进制，仅支持 {sorted(VALID_BASES)}")
    try:
        integer = int(value, from_base)
    except ValueError as exc:
        raise ConvertError(f"输入 '{value}' 不是有效的 {from_base} 进制数") from exc

    if to_base == 2:
        result = bin(integer)
    elif to_base == 8:
        result = oct(integer)
    elif to_base == 10:
        result = str(integer)
    else:
        result = hex(integer)
    return result.upper().replace("0X", "0x") if to_base == 16 else result


# --------------------------------------------------------------------------- #
# Unit conversion
# --------------------------------------------------------------------------- #

# Each category maps unit name -> conversion factor relative to the base unit.
# Value in base unit = value_in_unit * factor.
UNIT_FACTORS: dict[str, dict[str, float]] = {
    "length": {
        "mm": 0.001,
        "cm": 0.01,
        "m": 1.0,
        "km": 1000.0,
        "inch": 0.0254,
        "ft": 0.3048,
        "yd": 0.9144,
        "mile": 1609.344,
    },
    "weight": {
        "mg": 0.000001,
        "g": 0.001,
        "kg": 1.0,
        "t": 1000.0,
        "lb": 0.45359237,
        "oz": 0.028349523125,
    },
    "temperature": {},  # handled specially
    "area": {
        "mm2": 0.000001,
        "cm2": 0.0001,
        "m2": 1.0,
        "km2": 1_000_000.0,
        "ha": 10_000.0,
        "acre": 4046.8564224,
    },
    "volume": {
        "ml": 0.001,
        "l": 1.0,
        "m3": 1000.0,
        "cm3": 0.001,
        "gal": 3.785411784,
        "qt": 0.946352946,
        "pt": 0.473176473,
        "cup": 0.2365882365,
    },
    "time": {
        "ms": 0.001,
        "s": 1.0,
        "min": 60.0,
        "h": 3600.0,
        "day": 86400.0,
        "week": 604800.0,
    },
    "data": {
        "b": 1.0,
        "kb": 1024.0,
        "mb": 1024.0 ** 2,
        "gb": 1024.0 ** 3,
        "tb": 1024.0 ** 4,
    },
}

UNIT_CATEGORIES = list(UNIT_FACTORS.keys())


def list_units() -> dict[str, list[str]]:
    """Return the available unit categories and their units."""
    return {cat: list(units.keys()) for cat, units in UNIT_FACTORS.items()}


def _convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    # Convert to Celsius first.
    if from_unit == "c":
        celsius = value
    elif from_unit == "f":
        celsius = (value - 32) * 5 / 9
    elif from_unit == "k":
        celsius = value - 273.15
    else:
        raise ConvertError(f"未知温度单位: {from_unit}")

    if to_unit == "c":
        return celsius
    if to_unit == "f":
        return celsius * 9 / 5 + 32
    if to_unit == "k":
        return celsius + 273.15
    raise ConvertError(f"未知温度单位: {to_unit}")


def convert_unit(value: float, from_unit: str, to_unit: str, category: str) -> float:
    """Convert a numeric value between two units of the same category."""
    if category not in UNIT_FACTORS:
        raise ConvertError(f"未知单位类别: {category}")

    if category == "temperature":
        return _convert_temperature(value, from_unit, to_unit)

    units = UNIT_FACTORS[category]
    if from_unit not in units:
        raise ConvertError(f"类别 '{category}' 中无单位 '{from_unit}'")
    if to_unit not in units:
        raise ConvertError(f"类别 '{category}' 中无单位 '{to_unit}'")

    base_value = value * units[from_unit]
    return base_value / units[to_unit]
