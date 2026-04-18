"""
BPS Data Downloader — Configuration & Constants
================================================
Dimension ordering, color scheme, and shared settings.
"""

# ── Dimension order used by BPS to build datacontent keys ────────────────────
# key = str(vervar) + str(var) + str(turvar) + str(tahun) + str(turtahun)
DIMS_ORDER: list[str] = ["vervar", "var", "turvar", "tahun", "turtahun"]

# CSS class name + background hex for each dimension
DIMS_COLORS: dict[str, tuple[str, str]] = {
    "vervar":   ("seg-vervar",   "#dbeafe"),
    "var":      ("seg-var",      "#dcfce7"),
    "turvar":   ("seg-turvar",   "#fef9c3"),
    "tahun":    ("seg-tahun",    "#fce7f3"),
    "turtahun": ("seg-turtahun", "#f3e8ff"),
}

# Human-readable names shown in the legend
DIMS_LABELS: dict[str, str] = {
    "vervar":   "vervar (province / vertical var)",
    "var":      "var (variable)",
    "turvar":   "turvar (derived variable)",
    "tahun":    "tahun (year)",
    "turtahun": "turtahun (period)",
}

# Labels for dimension tables
DIM_TABLE_LABELS: dict[str, str] = {
    "subject":  "Subject",
    "var":      "Variable (var)",
    "turvar":   "Derived Variable (turvar)",
    "vervar":   "Vertical Variable",  # appended with labelvervar at runtime
    "tahun":    "Year (tahun)",
    "turtahun": "Period (turtahun)",
}
