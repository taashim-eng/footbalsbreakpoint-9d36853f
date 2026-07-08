"""
Data validation layer – runs between collection and feature engineering.

Checks schema integrity, completeness, foreign-key consistency, and
generates a human-readable data quality report.
"""

import os
import pandas as pd
import numpy as np
from typing import Optional


class DataValidator:
    """Validate the merged analysis dataset before feature engineering."""

    # ── expected schemas (column → dtype family) ────────────────────────
    MATCH_SCHEMA = {
        "match_id": "object",
        "competition": "object",
        "tournament_year": "int",
        "date": "object",
        "stage": "object",
        "team_home": "object",
        "team_away": "object",
        "score_home": "int",
        "score_away": "int",
    }

    EVENT_SCHEMA = {
        "match_id": "object",
        "minute": "int",
        "event_type": "object",
        "team": "object",
    }

    def __init__(self):
        self.issues: list[dict] = []
        self.stats: dict = {}

    # ── public API ───────────────────────────────────────────────────────

    def validate_matches(self, df: pd.DataFrame) -> bool:
        """Schema + basic integrity for the matches table."""
        self._check_schema(df, self.MATCH_SCHEMA, "matches")
        self._check_duplicates(df, "match_id", "matches")
        self._check_null_rate(df, "matches", threshold=0.05,
                              critical_cols=["match_id", "team_home", "team_away",
                                             "score_home", "score_away", "date"])

        # Score sanity
        neg = df[(df["score_home"] < 0) | (df["score_away"] < 0)]
        if len(neg):
            self._add("matches", "P0", f"{len(neg)} matches with negative scores")

        self.stats["total_matches"] = len(df)
        self.stats["tournaments"] = sorted(df["tournament_year"].unique().tolist())
        self.stats["competitions"] = sorted(df["competition"].unique().tolist())
        return len([i for i in self.issues if i["severity"] == "P0"]) == 0

    def validate_events(self, df: pd.DataFrame, match_ids: set) -> bool:
        """Validate events have matching match_ids and sensible minutes."""
        self._check_schema(df, self.EVENT_SCHEMA, "events")

        orphans = set(df["match_id"].unique()) - match_ids
        if orphans:
            self._add("events", "P1",
                       f"{len(orphans)} event match_ids not found in matches table")

        bad_min = df[(df["minute"] < 0) | (df["minute"] > 130)]
        if len(bad_min):
            self._add("events", "P1",
                       f"{len(bad_min)} events with minute outside 0-130")

        self.stats["total_events"] = len(df)
        return True

    def validate_gdp(self, df: pd.DataFrame) -> bool:
        """Validate GDP data coverage."""
        if df is None or len(df) == 0:
            self._add("gdp", "P0", "GDP dataframe is empty")
            return False
        self._check_null_rate(df, "gdp", threshold=0.10,
                              critical_cols=["country_iso3", "gdp_per_capita_ppp"])
        neg = df[df["gdp_per_capita_ppp"] <= 0]
        if len(neg):
            self._add("gdp", "P1", f"{len(neg)} rows with GDP <= 0")
        self.stats["gdp_countries"] = df["country_iso3"].nunique()
        return True

    def validate_weather(self, df: pd.DataFrame, match_ids: set) -> bool:
        """Validate weather data."""
        if df is None or len(df) == 0:
            self._add("weather", "P2", "Weather dataframe is empty – using defaults")
            return True
        orphans = set(df["match_id"].unique()) - match_ids
        if orphans:
            self._add("weather", "P2",
                       f"{len(orphans)} weather match_ids not found in matches")
        coverage = len(set(df["match_id"].unique()) & match_ids) / max(len(match_ids), 1)
        self.stats["weather_coverage"] = f"{coverage:.1%}"
        return True

    def validate_foreign_keys(
        self,
        events: pd.DataFrame,
        weather: Optional[pd.DataFrame],
        betting: Optional[pd.DataFrame],
        match_ids: set,
    ):
        """Cross-table FK checks."""
        for name, tbl in [("events", events), ("weather", weather), ("betting", betting)]:
            if tbl is not None and "match_id" in tbl.columns:
                orphans = set(tbl["match_id"].unique()) - match_ids
                if orphans:
                    self._add(name, "P2",
                              f"{len(orphans)} FK violations: match_ids missing in matches")

    def coverage_by_tournament(self, df: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
        """Compute data coverage % per tournament."""
        rows = []
        for year in sorted(df["tournament_year"].unique()):
            matches_year = df[df["tournament_year"] == year]
            mids = set(matches_year["match_id"])
            events_year = events[events["match_id"].isin(mids)] if events is not None else pd.DataFrame()
            goals_with_min = events_year[
                (events_year["event_type"] == "goal") & (events_year["minute"].notna())
            ] if len(events_year) else pd.DataFrame()

            rows.append({
                "tournament_year": year,
                "total_matches": len(matches_year),
                "matches_with_events": events_year["match_id"].nunique() if len(events_year) else 0,
                "goals_with_minute": len(goals_with_min),
                "minute_coverage_pct": (
                    events_year["match_id"].nunique() / max(len(matches_year), 1) * 100
                ) if len(events_year) else 0,
            })
        return pd.DataFrame(rows)

    def generate_report(self, path: str):
        """Write a human-readable markdown quality report."""
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        lines = ["# Data Quality Report\n"]
        lines.append(f"**Generated**: {pd.Timestamp.now().isoformat()}\n")

        lines.append("## Summary Statistics\n")
        for k, v in self.stats.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")

        if self.issues:
            lines.append("## Issues Found\n")
            lines.append("| Severity | Table | Description |")
            lines.append("|----------|-------|-------------|")
            for i in sorted(self.issues, key=lambda x: x["severity"]):
                lines.append(f"| {i['severity']} | {i['table']} | {i['description']} |")
        else:
            lines.append("## ✅ No Issues Found\n")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    # ── internals ────────────────────────────────────────────────────────

    def _check_schema(self, df: pd.DataFrame, schema: dict, table: str):
        missing = set(schema.keys()) - set(df.columns)
        if missing:
            self._add(table, "P0", f"Missing columns: {missing}")

    def _check_duplicates(self, df: pd.DataFrame, key_col: str, table: str):
        dups = df[df.duplicated(subset=[key_col], keep=False)]
        if len(dups):
            self._add(table, "P1",
                       f"{len(dups)} duplicate rows on '{key_col}'")

    def _check_null_rate(self, df: pd.DataFrame, table: str,
                          threshold: float, critical_cols: list[str]):
        for col in critical_cols:
            if col not in df.columns:
                continue
            rate = df[col].isna().mean()
            if rate > threshold:
                self._add(table, "P1",
                           f"Column '{col}' has {rate:.1%} null (threshold {threshold:.0%})")

    def _add(self, table: str, severity: str, description: str):
        self.issues.append({
            "table": table,
            "severity": severity,
            "description": description,
        })
