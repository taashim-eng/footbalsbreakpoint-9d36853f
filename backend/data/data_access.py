"""
Standardised data access layer.

All analysis scripts import data through this module so that the underlying
storage format (SQLite / Parquet / CSV) is abstracted away.
"""

import os
import sqlite3
from typing import Optional

import pandas as pd

from backend.config import DB_PATH, PROCESSED_DIR


class DataAccess:
    """Read-only interface to the processed analysis dataset."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._parquet_path = os.path.join(str(PROCESSED_DIR), "analysis_dataset.parquet")

    # ── convenience helpers ──────────────────────────────────────────────

    def _query(self, sql: str) -> pd.DataFrame:
        """Run a SQL query against the SQLite database."""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(
                f"Database not found at {self.db_path}. "
                "Run the pipeline first: python -m backend.data.pipeline"
            )
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(sql, conn)

    # ── table-level accessors ────────────────────────────────────────────

    def get_matches(
        self,
        era: Optional[str] = None,
        competition: Optional[str] = None,
    ) -> pd.DataFrame:
        clauses = ["1=1"]
        if era:
            era_map = {"A": "(2002,2006,2010)", "B": "(2014,2018,2022)", "C": "(2026)"}
            clauses.append(f"tournament_year IN {era_map.get(era, '()')}")
        if competition:
            clauses.append(f"competition = '{competition}'")
        where = " AND ".join(clauses)
        return self._query(f"SELECT * FROM matches WHERE {where}")

    def get_events(
        self,
        match_id: Optional[str] = None,
        minute_range: Optional[tuple[int, int]] = None,
    ) -> pd.DataFrame:
        clauses = ["1=1"]
        if match_id:
            clauses.append(f"match_id = '{match_id}'")
        if minute_range:
            clauses.append(f"minute >= {minute_range[0]} AND minute <= {minute_range[1]}")
        where = " AND ".join(clauses)
        return self._query(f"SELECT * FROM events WHERE {where}")

    def get_gdp(self) -> pd.DataFrame:
        return self._query("SELECT * FROM gdp")

    def get_weather(self, match_id: Optional[str] = None) -> pd.DataFrame:
        if match_id:
            return self._query(f"SELECT * FROM weather WHERE match_id = '{match_id}'")
        return self._query("SELECT * FROM weather")

    def get_rankings(self) -> pd.DataFrame:
        return self._query("SELECT * FROM rankings")

    def get_betting(self, match_id: Optional[str] = None) -> pd.DataFrame:
        where = f"WHERE match_id = '{match_id}'" if match_id else ""
        return self._query(f"SELECT * FROM betting {where}")

    # ── analysis-ready dataset ───────────────────────────────────────────

    def get_analysis_dataset(self, era: Optional[str] = None) -> pd.DataFrame:
        """
        Return the fully joined and feature-engineered dataset.

        Loads from Parquet for speed, falls back to SQLite.
        """
        if os.path.exists(self._parquet_path):
            df = pd.read_parquet(self._parquet_path)
        else:
            df = self._query("SELECT * FROM analysis_dataset")

        if era:
            era_map = {"A": [2002, 2006, 2010], "B": [2014, 2018, 2022], "C": [2026]}
            df = df[df["tournament_year"].isin(era_map.get(era, []))]
        return df

    def get_feature_matrix(
        self,
        target: str = "goals_conceded_post_break",
        exclude_betting: bool = True,
    ) -> tuple[pd.DataFrame, pd.Series]:
        """
        Return (X, y) ready for ML.

        Parameters
        ----------
        exclude_betting : bool
            If True, remove betting columns (for Stage 1 match-only model).
        """
        df = self.get_analysis_dataset()
        if target not in df.columns:
            raise ValueError(f"Target '{target}' not in dataset columns: {list(df.columns)}")

        y = df[target]

        # Drop target, ID, and metadata columns
        drop_cols = [
            target, "match_id", "date", "team_home", "team_away",
            "venue", "city", "_source", "competition",
        ]

        betting_cols = [
            c for c in df.columns
            if any(kw in c for kw in [
                "odds", "betting", "volume", "implied_prob",
                "clv", "handicap", "bookmaker",
            ])
        ]

        if exclude_betting:
            drop_cols.extend(betting_cols)

        X = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore")

        # Keep only numeric + bool columns
        X = X.select_dtypes(include=["number", "bool"])

        return X, y
