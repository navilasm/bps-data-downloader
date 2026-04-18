"""
BPS (Badan Pusat Statistik) Data Downloader
============================================
Streamlit app to fetch data from BPS Web API and decode
the datacontent key mapping.

Datacontent keys are string concatenations of parameter values:
    key = str(vervar) + str(var) + str(turvar) + str(tahun) + str(turtahun)

Example:
    960019543012561 = 9600 | 195 | 430 | 125 | 61
    → vervar=PAPUA TENGAH, var=Poverty Line, turvar=Urban Area,
      tahun=2025, turtahun=Semester 1 (March)
"""

import os
from typing import Any
from datetime import date

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

from config import DIMS_ORDER
from bps_api import (
    fetch_bps,
    resolve_url,
    year_to_bps_code,
    replace_th_in_url,
    url_has_th_segment,
)
from decoder import build_lookup, decode_datacontent
from components import (
    inject_css,
    render_response_overview,
    render_key_mapping,
    render_decoded_table,
    render_failed_keys,
)

# ── Load .env ────────────────────────────────────────────────────────────────
load_dotenv()
WEB_API_KEY = os.getenv("WebAPI_KEY")

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="BPS Data Downloader",
    page_icon="⬇️",
    layout="wide",
)

inject_css()

# ── Header ───────────────────────────────────────────────────────────────────

st.title("BPS Data Downloader")
st.caption(
    """Fetch data from the BPS Web API and explore how `datacontent` keys map to dimension parameters. Each `datacontent` ID is a concatenation of dimension values `key = vervar + var + turvar + tahun + turtahun`. The app decodes every key back into human-readable labels."""
)

# ── Session state defaults ───────────────────────────────────────────────────
if "bps_data" not in st.session_state:
    st.session_state.bps_data = None
if "all_year_results" not in st.session_state:
    st.session_state.all_year_results = None

# ── Sidebar: API URL input ───────────────────────────────────────────────────

with st.sidebar:
    st.header("API Request")

    if WEB_API_KEY:
        st.success("`WebAPI_KEY` loaded from `.env`", icon="✅")
        st.caption(
            "You can use `WebAPI_KEY` as a placeholder in your URL, e.g.:\n"
            "`https://webapi.bps.go.id/v1/api/list/.../key/WebAPI_KEY`"
        )
    else:
        st.warning(
            "No `WebAPI_KEY` found in `.env`. "
            "Please include your API key directly in the URL.",
            icon="⚠️",
        )

    api_url = st.text_area(
        "BPS API URL",
        placeholder=(
            "https://webapi.bps.go.id/v1/api/list/.../key/WebAPI_KEY"
            if WEB_API_KEY
            else "https://webapi.bps.go.id/v1/api/list/.../key/YOUR_API_KEY"
        ),
        height=150,
        help=(
            "Use `WebAPI_KEY` as the key value — it will be replaced automatically."
            if WEB_API_KEY
            else "Paste the full BPS Web API URL including your API key."
        ),
    )

    fetch_btn = st.button("Fetch Data", width="content", type="primary")

# ── Fetch single URL ─────────────────────────────────────────────────────────

if fetch_btn and api_url.strip():
    final_url = resolve_url(api_url, WEB_API_KEY)
    if final_url is None:
        st.error(
            "URL contains `WebAPI_KEY` but no key was found in `.env`. "
            "Please add `WebAPI_KEY=your_key` to a `.env` file or "
            "replace `WebAPI_KEY` with your actual API key."
        )
        st.stop()

    with st.spinner("Fetching data from BPS API…"):
        try:
            st.session_state.bps_data = fetch_bps(final_url)
            st.toast("Data fetched successfully!", icon="🎉")
        except requests.HTTPError as exc:
            st.error(f"HTTP error: {exc}")
        except requests.ConnectionError:
            st.error("Could not connect to the BPS API. Check the URL and your network.")
        except Exception as exc:
            st.error(f"Unexpected error: {exc}")

# ── Main content ─────────────────────────────────────────────────────────────

data = st.session_state.bps_data

if data is None:
    st.info("👈 Paste a BPS API URL in the sidebar and click **Fetch Data** to begin.")
    st.stop()

availability = data.get("data-availability", "?")

if availability == "list-not-available":
    st.error("Data is not available. Please check the API URL.")
    st.stop()

# 1) Response overview (badges, dimension tabs, notes, JSON preview)
render_response_overview(data)

# 2) Decode datacontent keys
datacontent: dict = data.get("datacontent", {})

if not datacontent:
    st.warning("No `datacontent` entries in the response.")
    st.stop()

lookup = build_lookup(data)
decoded_rows, failed_keys = decode_datacontent(datacontent, lookup)

# 3) Key anatomy visualisation
render_key_mapping(decoded_rows, failed_keys, lookup)

# 4) Decoded data table + CSV download
render_decoded_table(decoded_rows, failed_keys)


# ── Multi-year fetch logic ───────────────────────────────────────────────────

def _run_multi_year_fetch(base_url: str, start_year: int, end_year: int) -> None:
    """Fetch, decode, and concatenate data for a range of years.

    Results are stored in ``st.session_state.all_year_results`` so they
    persist across Streamlit reruns (e.g. when the download button is clicked).
    """
    all_decoded_rows: list[dict] = []
    all_failed_keys: list[str] = []
    skipped_years: list[int] = []
    years = list(range(start_year, end_year + 1))

    progress_bar = st.progress(0, text="Fetching year data…")

    for i, yr in enumerate(years):
        th_code = year_to_bps_code(yr)
        yr_url = replace_th_in_url(base_url, th_code)

        try:
            yr_data = fetch_bps(yr_url)
        except Exception as exc:
            st.warning(f"Year {yr} (th={th_code}): fetch failed — {exc}")
            skipped_years.append(yr)
            progress_bar.progress((i + 1) / len(years), text=f"Fetching {yr}… (error)")
            continue

        if yr_data.get("data-availability") == "list-not-available":
            skipped_years.append(yr)
            progress_bar.progress(
                (i + 1) / len(years), text=f"Fetching {yr}… (not available)"
            )
            continue

        yr_lookup = build_lookup(yr_data)
        yr_datacontent: dict = yr_data.get("datacontent", {})
        rows, fails = decode_datacontent(
            yr_datacontent, yr_lookup, extra_fields={"year_fetched": yr}
        )
        all_decoded_rows.extend(rows)
        all_failed_keys.extend(f"{yr}: {k}" for k in fails)

        progress_bar.progress((i + 1) / len(years), text=f"Fetched {yr} ✓")

    progress_bar.empty()

    # Store in session state so results survive reruns
    st.session_state.all_year_results = {
        "decoded_rows": all_decoded_rows,
        "failed_keys": all_failed_keys,
        "skipped_years": skipped_years,
        "total_years": len(years),
        "start_year": start_year,
        "end_year": end_year,
    }


# ── Download All Years ───────────────────────────────────────────────────────

with st.container(border=True):
    st.markdown("#### Download All Year")
    st.caption(
        "Iterate over a range of years, replacing the `/th/<code>` segment "
        "in the URL for each year. Years are converted to BPS codes "
        "(e.g. 1986 → 86, 2025 → 125)."
    )

    col1, col2, col3 = st.columns(3, vertical_alignment="bottom")
    
    current_year = date.today().year

    start_year = col1.number_input("Start Year", min_value=1960, max_value=current_year, value=current_year-5)
    end_year = col2.number_input("End Year", min_value=1960, max_value=current_year, value=current_year)
    fetch_all_btn = col3.button(
        "Fetch All Years", width="content", type="primary", key="fetch_all_years"
    )

    if fetch_all_btn:
        if not api_url.strip():
            st.error("Please enter a BPS API URL in the sidebar first.")
        elif start_year > end_year:
            st.error("Start year must be ≤ end year.")
        else:
            base_url = resolve_url(api_url, WEB_API_KEY)
            if base_url is None:
                st.error("URL contains `WebAPI_KEY` but no key was found in `.env`.")
            elif not url_has_th_segment(base_url):
                st.error(
                    "URL does not contain a `/th/<number>` segment. "
                    "Make sure your URL includes e.g. `/th/86/` so the year can be swapped."
                )
            else:
                _run_multi_year_fetch(base_url, start_year, end_year)

    # ── Render persisted results (survives reruns) ───────────────────────
    results = st.session_state.all_year_results
    if results is not None:
        all_decoded_rows = results["decoded_rows"]
        all_failed_keys = results["failed_keys"]
        skipped_years = results["skipped_years"]
        total_years = results["total_years"]
        r_start = results["start_year"]
        r_end = results["end_year"]

        st.markdown(
            f"**Done!** {len(all_decoded_rows)} rows decoded across "
            f"{total_years - len(skipped_years)} year(s). "
            f"{len(skipped_years)} year(s) skipped."
        )

        if skipped_years:
            st.info(f"Skipped years (no data): {', '.join(str(y) for y in skipped_years)}")

        if all_decoded_rows:
            df_all = pd.DataFrame(all_decoded_rows)
            label_cols_all = [c for c in df_all.columns if c.endswith("_label")]
            display_cols_all = ["year_fetched", "key"] + label_cols_all + ["value"]
            display_cols_all = [c for c in display_cols_all if c in df_all.columns]

            st.dataframe(df_all[display_cols_all], width='stretch', hide_index=True)

            csv_all = df_all[display_cols_all].to_csv(index=False)
            st.download_button(
                "Download All-Year CSV",
                data=csv_all,
                file_name=f"bps_data_{r_start}_{r_end}.csv",
                mime="text/csv",
                width="content",
                type="primary",
                key="download_all_years",
            )

        render_failed_keys(all_failed_keys, label="all years")

# 5) Failed keys from the single-fetch decode
render_failed_keys(failed_keys)