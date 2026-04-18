"""
BPS Data Downloader — API Utilities
====================================
HTTP fetching, URL resolution (WebAPI_KEY), and year-code helpers.
"""

import re
from typing import Any

import requests


def fetch_bps(url: str) -> dict[str, Any]:
    """Fetch JSON from a BPS API endpoint."""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ── URL helpers ──────────────────────────────────────────────────────────────

def resolve_url(raw_url: str, api_key: str | None) -> str | None:
    """Replace the ``WebAPI_KEY`` placeholder with the real key.

    Returns the resolved URL, or ``None`` if the placeholder is present
    but no key is available.
    """
    url = raw_url.strip()
    if api_key and "WebAPI_KEY" in url:
        return url.replace("WebAPI_KEY", api_key)
    if not api_key and "WebAPI_KEY" in url:
        return None  # caller should show an error
    return url


def year_to_bps_code(year: int) -> int:
    """Convert a calendar year to the BPS ``/th/`` code (year − 1900).

    Examples: 1986 → 86, 2000 → 100, 2025 → 125, 2026 → 126.
    """
    return year - 1900


def replace_th_in_url(url: str, th_value: int) -> str:
    """Replace the ``/th/<number>`` segment in a BPS API URL with *th_value*."""
    return re.sub(r"/th/\d+", f"/th/{th_value}", url)


def url_has_th_segment(url: str) -> bool:
    """Return True if *url* contains a ``/th/<digits>`` segment."""
    return bool(re.search(r"/th/\d+", url))
