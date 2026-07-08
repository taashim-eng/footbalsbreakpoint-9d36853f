"""
GDP per capita (PPP, current international $) collector.

Primary source : World Bank via the *wbgapi* package.
Fallback       : Hardcoded reference table covering 60+ countries for
                 World Cup tournament years (2002-2025).

Output columns : country_iso3, year, gdp_per_capita_ppp, _source
"""

import numpy as np
import pandas as pd

from backend.data.collectors.base_collector import BaseCollector
from backend import config

# ── Hardcoded fallback data ──────────────────────────────────────────────────
# Columns: ISO3 → {year: GDP per capita PPP (current int'l $)}
# Years align with World Cup cycles: 2002, 2006, 2010, 2014, 2018, 2022, 2025
_FALLBACK_YEARS = [2002, 2006, 2010, 2014, 2018, 2022, 2025]

_FALLBACK: dict[str, list[float]] = {
    # ── Americas ─────────────────────────────────────────────────────────
    "USA": [38000, 47000, 49000, 55000, 63000, 76000, 85000],
    "CAN": [31000, 37000, 40000, 45000, 49000, 55000, 60000],
    "MEX": [9500, 12000, 14000, 16500, 19000, 20000, 22000],
    "BRA": [7500, 9800, 14000, 16000, 15500, 16000, 17500],
    "ARG": [8000, 12000, 18000, 20000, 20500, 22000, 24000],
    "COL": [5500, 7500, 9500, 12500, 14500, 15000, 17000],
    "URY": [7500, 10000, 14000, 20000, 22000, 23000, 25000],
    "CHL": [9500, 13000, 16500, 22000, 25000, 27000, 30000],
    "PER": [4500, 6000, 9000, 11500, 13500, 14000, 16000],
    "ECU": [5000, 7000, 9000, 11000, 11500, 12000, 13500],
    "PRY": [3500, 4500, 7000, 9000, 12000, 13500, 15000],
    "CRI": [7000, 9500, 12000, 15000, 17500, 19000, 21000],
    "PAN": [7000, 10000, 14000, 20000, 25000, 28000, 31000],
    "JAM": [6000, 7000, 8000, 8500, 9000, 9500, 10500],
    "HND": [3000, 3500, 4200, 4800, 5300, 5500, 6200],
    "BOL": [2800, 3500, 4500, 6500, 8000, 8500, 9500],

    # ── Europe ───────────────────────────────────────────────────────────
    "GBR": [28000, 35000, 37000, 43000, 46000, 52000, 58000],
    "FRA": [27000, 33000, 37000, 42000, 46000, 50000, 55000],
    "DEU": [28000, 34000, 40000, 47000, 53000, 58000, 63000],
    "ESP": [22000, 28000, 32000, 33000, 39000, 42000, 47000],
    "ITA": [26000, 30000, 34000, 36000, 40000, 44000, 48000],
    "PRT": [18000, 22000, 26000, 28000, 33000, 37000, 40000],
    "NLD": [31000, 38000, 43000, 49000, 56000, 62000, 67000],
    "BEL": [28000, 34000, 38000, 43000, 48000, 54000, 59000],
    "HRV": [11000, 15000, 19000, 21000, 25000, 30000, 34000],
    "SRB": [4500, 8000, 11500, 13500, 16000, 19000, 22000],
    "DNK": [30000, 37000, 42000, 48000, 55000, 62000, 68000],
    "CHE": [36000, 43000, 52000, 60000, 66000, 72000, 78000],
    "AUT": [30000, 36000, 42000, 47000, 53000, 58000, 63000],
    "POL": [10000, 14000, 19000, 24000, 29000, 35000, 40000],
    "CZE": [16000, 21000, 26000, 30000, 36000, 42000, 47000],
    "SWE": [29000, 36000, 41000, 47000, 53000, 59000, 64000],
    "NOR": [36000, 50000, 56000, 66000, 65000, 67000, 72000],
    "UKR": [3500, 5500, 7000, 8700, 8500, 9000, 10500],
    "RUS": [8000, 14000, 19000, 24000, 25000, 28000, 31000],
    "TUR": [8000, 13000, 16000, 21000, 27000, 30000, 35000],

    # ── Asia ─────────────────────────────────────────────────────────────
    "JPN": [27000, 33000, 35000, 38000, 42000, 42000, 45000],
    "KOR": [18000, 24000, 29000, 34000, 40000, 47000, 52000],
    "CHN": [3000, 5500, 9000, 13000, 17000, 21000, 24000],
    "IND": [1800, 2700, 3800, 5400, 7200, 8500, 10000],
    "IDN": [3000, 4200, 6500, 9500, 12000, 14000, 16000],
    "THA": [5500, 8000, 11000, 14500, 17000, 18000, 20000],
    "VNM": [1800, 2600, 4000, 5500, 7500, 10000, 12500],
    "PHL": [2800, 3700, 4800, 6800, 8300, 9500, 11000],
    "MYS": [10000, 14000, 17000, 24000, 28000, 30000, 34000],
    "SGP": [36000, 48000, 56000, 76000, 90000, 102000, 115000],
    "SAU": [18000, 24000, 34000, 48000, 48000, 50000, 52000],
    "IRN": [7000, 10000, 13000, 15000, 13000, 14000, 15500],
    "QAT": [60000, 78000, 100000, 130000, 95000, 85000, 90000],

    # ── Africa ───────────────────────────────────────────────────────────
    "MAR": [3000, 4000, 5200, 7200, 8000, 8500, 9500],
    "SEN": [1500, 1900, 2200, 2600, 3300, 3700, 4200],
    "CMR": [1900, 2300, 2700, 3200, 3600, 3800, 4200],
    "NGA": [1600, 2800, 4500, 5700, 5500, 5000, 5500],
    "GHA": [1500, 2200, 3200, 4200, 5000, 5500, 6200],
    "TUN": [6000, 7500, 9000, 10500, 11000, 11500, 12500],
    "EGY": [4000, 5500, 8500, 10000, 12000, 13000, 15000],
    "ZAF": [6500, 9000, 11000, 13000, 13500, 14000, 15500],
    "DZA": [5500, 7500, 10000, 13000, 12000, 12500, 13500],
    "CIV": [1800, 2100, 2500, 3200, 4200, 5000, 5800],

    # ── Oceania ──────────────────────────────────────────────────────────
    "AUS": [28000, 34000, 38000, 45000, 50000, 55000, 60000],
    "NZL": [22000, 27000, 30000, 35000, 40000, 44000, 48000],
}


class GDPCollector(BaseCollector):
    """Collect GDP per capita (PPP) for World Cup countries."""

    def __init__(self):
        super().__init__("gdp", str(config.RAW_DIR))

    # ── Public API ───────────────────────────────────────────────────────

    def collect(self, force: bool = False) -> pd.DataFrame:
        """Return a long-format DataFrame of GDP per capita PPP.

        Tries the World Bank API first, then falls back to a hardcoded
        reference table.  Results are cached as Parquet.
        """
        cache_key = "all"
        if not force and self._is_cache_valid(cache_key):
            self._log("returning cached GDP data")
            return self._read_cache(cache_key)

        df = self._try_world_bank()
        if df is None or df.empty:
            self._log("World Bank unavailable – using hardcoded fallback")
            df = self._build_fallback()

        df = self._interpolate(df)
        df = df.sort_values(["country_iso3", "year"]).reset_index(drop=True)
        self._write_cache(df, cache_key)
        self._log(f"cached {len(df)} rows ({df['country_iso3'].nunique()} countries)")
        return df

    # ── World Bank source ────────────────────────────────────────────────

    def _try_world_bank(self) -> pd.DataFrame | None:
        """Attempt to pull GDP per capita PPP from the World Bank API."""
        try:
            import wbgapi as wb  # type: ignore

            self._log("fetching GDP data from World Bank …")
            raw = wb.data.DataFrame(
                "NY.GDP.PCAP.PP.CD", time=range(2001, 2027)
            )
            # raw comes as countries × years (wide).  Reshape to long.
            raw = raw.reset_index()
            id_col = raw.columns[0]  # usually 'economy'
            long = raw.melt(id_vars=[id_col], var_name="year_raw", value_name="gdp_per_capita_ppp")
            long = long.rename(columns={id_col: "country_iso3"})

            # year column arrives as e.g. "YR2022" → extract int
            long["year"] = (
                long["year_raw"]
                .astype(str)
                .str.extract(r"(\d{4})", expand=False)
                .astype(int)
            )
            long = long.drop(columns=["year_raw"])
            long = long.dropna(subset=["gdp_per_capita_ppp"])
            long["_source"] = "world_bank"
            self._log(f"received {len(long)} rows from World Bank")
            return long[["country_iso3", "year", "gdp_per_capita_ppp", "_source"]]

        except Exception as exc:  # noqa: BLE001
            self._log(f"World Bank fetch failed: {exc}")
            return None

    # ── Hardcoded fallback ───────────────────────────────────────────────

    @staticmethod
    def _build_fallback() -> pd.DataFrame:
        """Expand the hardcoded dict into a long-format DataFrame."""
        rows: list[dict] = []
        for iso3, values in _FALLBACK.items():
            for yr, val in zip(_FALLBACK_YEARS, values):
                rows.append(
                    {
                        "country_iso3": iso3,
                        "year": yr,
                        "gdp_per_capita_ppp": float(val),
                        "_source": "hardcoded_fallback",
                    }
                )
        return pd.DataFrame(rows)

    # ── Interpolation ────────────────────────────────────────────────────

    @staticmethod
    def _interpolate(df: pd.DataFrame) -> pd.DataFrame:
        """Linearly interpolate missing years between each country's min/max."""
        parts: list[pd.DataFrame] = []
        for iso3, grp in df.groupby("country_iso3"):
            yr_min, yr_max = int(grp["year"].min()), int(grp["year"].max())
            full_years = pd.DataFrame({"year": range(yr_min, yr_max + 1)})
            merged = full_years.merge(grp, on="year", how="left")
            merged["country_iso3"] = iso3
            merged["gdp_per_capita_ppp"] = (
                merged["gdp_per_capita_ppp"].interpolate(method="linear")
            )
            merged["_source"] = merged["_source"].fillna(
                merged["_source"].dropna().iloc[0] if not merged["_source"].dropna().empty else "interpolated"
            )
            parts.append(merged)
        return pd.concat(parts, ignore_index=True)
