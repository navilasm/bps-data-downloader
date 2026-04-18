# BPS Data Downloader

A Streamlit app to fetch data from the [BPS (Badan Pusat Statistik) Web API](https://webapi.bps.go.id/) within the `https://webapi.bps.go.id/v1/api/list` endpoint and decode the cryptic `datacontent` key mapping into human-readable labels.

[Link to Streamlit App](https://bps-data-downloader.streamlit.app/)

## What It Does

The BPS API returns data values keyed by concatenated dimension IDs:

```
key = str(vervar) + str(var) + str(turvar) + str(tahun) + str(turtahun)
```

For example, **`960019543012561`** breaks down as:

| Segment | Dimension | Value | Label |
|---------|-----------|-------|-------|
| `9600` | vervar | 9600 | PAPUA TENGAH |
| `195` | var | 195 | Poverty Line |
| `430` | turvar | 430 | Urban Area |
| `125` | tahun | 125 | 2025 |
| `61` | turtahun | 61 | Semester 1 (March) |

By **automatically decodes every key** back into its constituent parts, the app makes it easy to understand the data structure and lets you fetch **multiple years of the same report in one go**, automatically combining them into a single clean dataset. Instead of downloading and manually merging multiple Excel files, you get a ready-to-use, fully decoded dataset in one step.


### Features

- **Single URL fetch** — paste a BPS API URL and instantly decode all datacontent keys
- **Multi-year fetch** — iterate over a year range, automatically swapping the `/th/<code>` URL segment for each year
- **API key from `.env`** — store your key once and use `WebAPI_KEY` as a placeholder in URLs
- **Color-coded key anatomy** — visual breakdown showing how each key segment maps to a dimension
- **Dimension explorer** — tabbed tables for all dimension parameters (vervar, var, turvar, tahun, turtahun)
- **CSV download** — export decoded data for both single and multi-year fetches

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. (Optional) Set up your API key

Create a `.env` file in the project root:

```env
WebAPI_KEY=your_api_key_here
```

If set, you can use `WebAPI_KEY` as a placeholder in your URLs instead of pasting the raw key each time:

```
https://webapi.bps.go.id/v1/api/list/model/data/lang/ind/domain/0000/var/543/th/86/key/WebAPI_KEY
```

If not set, just paste the full URL with your API key directly.

### 3. Run the app

```bash
streamlit run app.py
```

## Usage

1. **Paste a BPS API URL** in the sidebar
2. Click **Fetch Data** to retrieve and decode the response
3. Explore the **dimension parameters**, **key anatomy**, and **decoded data table**
4. Use **Download All Year** to batch-fetch across a year range — the app swaps the `/th/<code>` segment automatically (year code = year − 1900, e.g. `1986 → 86`, `2025 → 125`)
5. **Download CSV** for single or multi-year results

## Project Structure

```
bps-data-downloader/
├── app.py            # Main Streamlit app — page layout and orchestration
├── config.py         # Constants: dimension ordering, color scheme, labels
├── bps_api.py        # API fetching, URL resolution, year-code helpers
├── decoder.py        # Datacontent key decoding and lookup building
├── components.py     # Reusable Streamlit UI components and HTML builders
├── requirements.txt  # Python dependencies
├── .env              # (optional) WebAPI_KEY=your_key
└── README.md
```

| Module | Responsibility |
|--------|---------------|
| `config.py` | `DIMS_ORDER`, `DIMS_COLORS`, `DIMS_LABELS`, `DIM_TABLE_LABELS` |
| `bps_api.py` | `fetch_bps()`, `resolve_url()`, `year_to_bps_code()`, `replace_th_in_url()` |
| `decoder.py` | `build_lookup()`, `decode_key()`, `decode_datacontent()` |
| `components.py` | `inject_css()`, `render_response_overview()`, `render_key_mapping()`, `render_decoded_table()`, `render_failed_keys()` |
| `app.py` | Page config, sidebar, fetch logic, section orchestration |

## Requirements

- Python 3.10+
- See `requirements.txt` for packages:
  - `streamlit >= 1.30.0`
  - `requests >= 2.31.0`
  - `pandas >= 2.0.0`
  - `python-dotenv >= 1.0.0`
