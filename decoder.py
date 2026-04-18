"""
BPS Data Downloader — Datacontent Key Decoder
==============================================
Build dimension lookups and decompose concatenated datacontent keys
back into their constituent dimension values.
"""

from typing import Any

from config import DIMS_ORDER


def build_lookup(data: dict) -> dict[str, dict[str, str]]:
    """Build val→label lookup dicts for each dimension present in *data*."""
    lookup: dict[str, dict[str, str]] = {}
    for dim in DIMS_ORDER:
        items = data.get(dim, [])
        if isinstance(items, list):
            lookup[dim] = {
                str(item["val"]): item.get("label", str(item["val"]))
                for item in items
            }
        else:
            lookup[dim] = {}
    return lookup


def decode_key(key: str, lookup: dict[str, dict[str, str]]) -> dict[str, dict[str, str]] | None:
    """Recursively decompose a datacontent key into its constituent
    dimension values by trying every valid prefix at each stage.

    Returns ``{dim_name: {"val": ..., "label": ...}}`` or ``None``.
    """
    dims = [d for d in DIMS_ORDER if lookup.get(d)]  # only dims present

    def _solve(remaining: str, idx: int) -> dict | None:
        if idx == len(dims):
            return {} if remaining == "" else None
        dim = dims[idx]
        for val_str, label in lookup[dim].items():
            if remaining.startswith(val_str):
                rest = _solve(remaining[len(val_str):], idx + 1)
                if rest is not None:
                    rest[dim] = {"val": val_str, "label": label}
                    return rest
        return None

    return _solve(key, 0)


def decode_datacontent(
    datacontent: dict,
    lookup: dict[str, dict[str, str]],
    *,
    extra_fields: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Decode all datacontent entries and return (decoded_rows, failed_keys).

    Parameters
    ----------
    datacontent : dict
        The ``datacontent`` mapping from the BPS API response.
    lookup : dict
        Dimension lookup as returned by :func:`build_lookup`.
    extra_fields : dict, optional
        Extra key-value pairs to inject into every decoded row
        (e.g. ``{"year_fetched": 2025}``).
    """
    decoded_rows: list[dict[str, Any]] = []
    failed_keys: list[str] = []

    for raw_key, value in datacontent.items():
        parts = decode_key(str(raw_key), lookup)
        if parts is not None:
            row: dict[str, Any] = {}
            if extra_fields:
                row.update(extra_fields)
            row["key"] = raw_key
            for dim in DIMS_ORDER:
                if dim in parts:
                    row[f"{dim}_val"] = parts[dim]["val"]
                    row[f"{dim}_label"] = parts[dim]["label"]
            row["value"] = value
            decoded_rows.append(row)
        else:
            failed_keys.append(str(raw_key))

    return decoded_rows, failed_keys
