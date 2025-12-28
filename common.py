#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Built-in modules
import math
from typing import Any


###############################################################################
def split_thousands(value: Any, decimals: int = 2) -> str:
    """
    Format a number using apostrophes as thousands separators.

    - None / NaN -> "0"
    - Integers show no decimal part
    - Floats are formatted up to `decimals` decimal places (trimmed)

    >>> split_thousands(1000012)
    "1'000'012"
    """

    if value is None:
        return "0"

    # If it's a string, try to parse as a number.
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return "0"
        try:
            value = float(s)
        except ValueError:
            return value

    # Integers
    if isinstance(value, int) and not isinstance(value, bool):
        return f"{value:,}".replace(",", "'")

    # Floats
    if isinstance(value, float):
        if math.isnan(value):
            return "0"
        if math.isinf(value):
            return str(value)
        if value.is_integer():
            return f"{int(value):,}".replace(",", "'")
        # It is an actual float
        fmt = f"{{:,.{decimals}f}}"
        out = fmt.format(value)
        if decimals > 0:
            out = out.rstrip("0").rstrip(".")
        return out.replace(",", "'")

    # Fallback: try numeric conversion.
    try:
        return split_thousands(float(value), decimals=decimals)
    except Exception:
        return str(value)
