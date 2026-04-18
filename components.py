"""
BPS Data Downloader — Reusable UI Components
=============================================
HTML builders and Streamlit rendering helpers.
"""

import json
from typing import Any

import pandas as pd
import streamlit as st

from config import DIMS_ORDER, DIMS_COLORS, DIMS_LABELS, DIM_TABLE_LABELS
from decoder import decode_key


# ── Custom CSS (injected once) ───────────────────────────────────────────────

CUSTOM_CSS = """
<style>
    /* ── Key anatomy ── */
    .key-anatomy {
        font-family: 'Fira Mono', 'Consolas', monospace;
        font-size: 1.05rem;
        letter-spacing: 0.5px;
    }
    .seg-vervar  { background:#dbeafe; color:#1e40af; padding:2px 4px; border-radius:4px; }
    .seg-var     { background:#dcfce7; color:#166534; padding:2px 4px; border-radius:4px; }
    .seg-turvar  { background:#fef9c3; color:#854d0e; padding:2px 4px; border-radius:4px; }
    .seg-tahun   { background:#fce7f3; color:#9d174d; padding:2px 4px; border-radius:4px; }
    .seg-turtahun{ background:#f3e8ff; color:#6b21a8; padding:2px 4px; border-radius:4px; }

    /* ── Legend pills ── */
    .legend { display:flex; gap:12px; flex-wrap:wrap; margin-bottom:12px; font-size:0.82rem; }
    .legend span { padding:3px 10px; border-radius:20px; font-weight:500; }
</style>
"""


def inject_css() -> None:
    """Inject custom CSS into the Streamlit page (call once)."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ── HTML builders ────────────────────────────────────────────────────────────

def key_anatomy_html(key: str, parts: dict[str, dict[str, str]]) -> str:
    """Build an HTML snippet that color-codes each segment of the key."""
    html = '<span class="key-anatomy">'
    for dim in DIMS_ORDER:
        if dim not in parts:
            continue
        val = parts[dim]["val"]
        css = DIMS_COLORS[dim][0]
        html += f'<span class="{css}">{val}</span>'
    html += "</span>"
    return html


def legend_html() -> str:
    """Build the color-coded legend bar."""
    parts = []
    for dim, (css, _bg) in DIMS_COLORS.items():
        parts.append(f'<span class="{css}">{DIMS_LABELS[dim]}</span>')
    return '<div class="legend">' + "".join(parts) + "</div>"


# ── Section renderers ────────────────────────────────────────────────────────

def render_response_overview(data: dict) -> None:
    """Render the status badges and variable title."""
    availability = data.get("data-availability", "?")
    last_update = data.get("last_update", "?")

    with st.container(border=True):
        if availability == "available":
            st.markdown(f"#### {data.get('var')[0].get('label')}")
            st.markdown(
                f":green-badge[:material/check: {availability}] "
                f":gray-badge[last update: {last_update}]"
            )
        else:
            st.markdown(
                f":red-badge[:material/close: {availability}] "
                f":gray-badge[last update: {last_update}]"
            )

        _render_dimension_tabs(data)
        _render_var_notes(data)
        _render_json_preview(data)


def _render_dimension_tabs(data: dict) -> None:
    """Show compact dimension parameter tables in tabs."""
    st.markdown("##### Dimension Parameters")

    dim_labels = dict(DIM_TABLE_LABELS)
    # Append dynamic labelvervar if present
    if data.get("labelvervar"):
        dim_labels["vervar"] = f"Vertical Variable — {data['labelvervar']}"

    available = [(k, v) for k, v in dim_labels.items() if data.get(k)]
    if not available:
        return

    tabs = st.tabs([v for _k, v in available])
    for tab, (dim_key, _dim_title) in zip(tabs, available):
        items = data[dim_key]
        with tab:
            if isinstance(items, list) and len(items) > 0:
                df = pd.DataFrame(items)
                cols_order = ["val", "label"] + [
                    c for c in df.columns if c not in ("val", "label")
                ]
                df = df[cols_order]
                st.dataframe(df, width="content", hide_index=True)
            else:
                st.write(items)


def _render_var_notes(data: dict) -> None:
    """Render any variable notes."""
    for v in data.get("var", []):
        note = v.get("note", "")
        if note and note.strip():
            st.markdown("###### Variable notes")
            st.markdown(note, unsafe_allow_html=True)


def _render_json_preview(data: dict) -> None:
    """Collapsible raw JSON preview."""
    with st.expander("Preview JSON"):
        with st.container(height=300, border=False):
            st.code(
                json.dumps(data, indent=2, ensure_ascii=False),
                language="json",
                width="content",
            )


def render_key_mapping(
    decoded_rows: list[dict],
    failed_keys: list[str],
    lookup: dict[str, dict[str, str]],
) -> None:
    """Render the datacontent key-mapping section with anatomy example."""
    with st.container(border=True):
        st.markdown("##### Datacontent Key Mapping")
        st.markdown(legend_html(), unsafe_allow_html=True)

        if not decoded_rows:
            return

        # Visual anatomy for a sample key
        sample = decoded_rows[0]
        sample_key = sample["key"]
        sample_parts = decode_key(sample_key, lookup)
        if sample_parts:
            st.markdown("###### Example key breakdown")
            st.markdown(key_anatomy_html(sample_key, sample_parts), unsafe_allow_html=True)

            detail_cols = st.columns(len(sample_parts))
            for col, dim in zip(detail_cols, DIMS_ORDER):
                if dim in sample_parts:
                    with col:
                        st.caption(dim)
                        st.code(f"{sample_parts[dim]['val']}  →  {sample_parts[dim]['label']}")


def render_decoded_table(
    decoded_rows: list[dict],
    failed_keys: list[str],
    *,
    download_filename: str = "bps_datacontent_decoded.csv",
    checkbox_key: str = "show_labels_single",
) -> None:
    """Render the decoded data table with download button."""
    with st.container(border=True):
        st.markdown("#### Final Data")
        st.markdown(
            f"**All entries** — {len(decoded_rows)} decoded, "
            f"{len(failed_keys)} unresolved"
        )

        if not decoded_rows:
            return

        df_decoded = pd.DataFrame(decoded_rows)
        label_cols = [c for c in df_decoded.columns if c.endswith("_label")]
        val_cols = [c for c in df_decoded.columns if c.endswith("_val")]
        show_labels = st.checkbox(
            "Show label columns only (hide raw val IDs)",
            value=True,
            key=checkbox_key,
        )

        if show_labels:
            display_cols = ["key"] + label_cols + ["value"]
        else:
            display_cols = (
                ["key"]
                + [c for pair in zip(label_cols, val_cols) for c in pair]
                + ["value"]
            )
        display_cols = [c for c in display_cols if c in df_decoded.columns]
        st.dataframe(df_decoded[display_cols], width="content", hide_index=True)

        csv_data = df_decoded[display_cols].to_csv(index=False)
        st.download_button(
            "Download Decoded CSV",
            data=csv_data,
            file_name=download_filename,
            mime="text/csv",
            width="content",
            type="primary",
        )


def render_failed_keys(failed_keys: list[str], *, label: str = "") -> None:
    """Render an expander listing keys that could not be decoded."""
    if not failed_keys:
        return
    suffix = f" ({label})" if label else ""
    with st.expander(f"⚠️ {len(failed_keys)} keys could not be decoded{suffix}"):
        st.write("These keys did not match the expected dimension concatenation pattern:")
        st.code("\n".join(failed_keys))
