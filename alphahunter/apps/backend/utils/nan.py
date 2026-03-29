"""Shared NaN / Infinity sanitisation helper.

Used by NanSafeJSONResponse in main.py and coerce_json() in api/presenters.py
to ensure yfinance floats never reach the wire as bare NaN/Infinity tokens.
"""
import math


def sanitize_nan(obj):
    """Recursively replace NaN / Infinity floats with None."""
    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, dict):
        return {k: sanitize_nan(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize_nan(v) for v in obj]
    return obj
