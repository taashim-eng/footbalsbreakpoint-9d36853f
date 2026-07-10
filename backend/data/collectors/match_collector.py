"""
Collector for FIFA World Cup match data.

Sources
-------
1. Historical (2002-2022) – Downloaded from the jfjelstul/worldcup GitHub
   repository CSV and filtered to year >= 2002.
2. Real 2026 results – Observed completed matches (group stage through the
   Round of 16) scraped from ESPN / FIFA.com, persisted as the artifact
   ``backend/data/raw/wc2026_results.json`` (see build_wc2026_results.py).
   Only matches that had actually been played are included; unplayed
   fixtures are never synthesised.
"""

import hashlib
import json
import os

import pandas as pd

from backend.data.collectors.base_collector import BaseCollector
from backend import config

# ── Constants ────────────────────────────────────────────────────────────────

_HISTORICAL_URL = (
    "https://raw.githubusercontent.com/jfjelstul/worldcup/master/"
    "data-csv/matches.csv"
)

_HISTORICAL_MIN_YEAR = 2002

_OUTPUT_COLUMNS = [
    "match_id", "competition", "tournament_year", "date", "stage",
    "team_home", "team_away", "score_home", "score_away",
    "venue", "city", "latitude", "longitude", "referee", "_source",
]


# ── Helper ───────────────────────────────────────────────────────────────────

def _make_match_id(
    date_str: str, team1: str, team2: str, competition: str = "World Cup"
) -> str:
    """Deterministic 16-char hex ID based on date, sorted teams, competition."""
    from backend.data.match_id_resolver import MatchIDResolver
    resolver = MatchIDResolver()
    t1 = resolver.canonical(team1)
    t2 = resolver.canonical(team2)
    teams = sorted([t1, t2])
    raw = f"{date_str}|{teams[0]}|{teams[1]}|{competition}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ── 2026 results (observed) ──────────────────────────────────────────────────

_WC2026_RESULTS_PATH = os.path.join(
    str(config.RAW_DIR), "wc2026_results.json"
)


# ── Collector ────────────────────────────────────────────────────────────────

class MatchCollector(BaseCollector):
    """Collects World Cup match data from historical CSV and 2026 fixtures."""

    def __init__(self):
        super().__init__("matches", str(config.RAW_DIR))

    # ── Public API ───────────────────────────────────────────────────────

    def collect(self, force: bool = False) -> pd.DataFrame:
        """Return a unified DataFrame of all World Cup matches.

        Uses Parquet caching with key ``'all'``.  Pass *force=True* to
        re-download / rebuild from scratch.
        """
        cache_key = "all"

        if not force and self._is_cache_valid(cache_key):
            self._log("Returning cached match data.")
            return self._read_cache(cache_key)

        # 1) Historical data (2002-2022)
        hist_df = self._fetch_historical()

        # 2) Real observed 2026 results (played matches only)
        wc_df = self._load_real_2026()

        # 3) Merge
        df = pd.concat([hist_df, wc_df], ignore_index=True)

        # Ensure column order
        for col in _OUTPUT_COLUMNS:
            if col not in df.columns:
                df[col] = None
        df = df[_OUTPUT_COLUMNS]

        self._write_cache(df, cache_key)
        self._log(f"Collected {len(df)} matches ({len(hist_df)} historical "
                  f"+ {len(wc_df)} observed 2026).")
        return df

    # ── Private helpers ──────────────────────────────────────────────────

    def _fetch_historical(self) -> pd.DataFrame:
        """Download the jfjelstul/worldcup CSV and filter to 2002+."""
        try:
            self._log(f"Downloading historical data from {_HISTORICAL_URL}")
            raw = pd.read_csv(_HISTORICAL_URL)
        except Exception as exc:
            self._log(f"Failed to download historical data: {exc}")
            return pd.DataFrame(columns=_OUTPUT_COLUMNS)

        # Normalise column names (the CSV uses snake_case already)
        raw.columns = [c.strip().lower() for c in raw.columns]

        # Extract year from the 'year' column or 'tournament_id'
        if "year" in raw.columns:
            raw = raw[raw["year"] >= _HISTORICAL_MIN_YEAR].copy()
            raw["tournament_year"] = raw["year"]
        elif "tournament_year" in raw.columns:
            raw = raw[raw["tournament_year"] >= _HISTORICAL_MIN_YEAR].copy()
        elif "tournament_id" in raw.columns:
            raw["year"] = raw["tournament_id"].apply(lambda x: int(str(x).split("-")[1]) if "-" in str(x) else 2022)
            raw = raw[raw["year"] >= _HISTORICAL_MIN_YEAR].copy()
            raw["tournament_year"] = raw["year"]
        else:
            self._log("Could not determine tournament year column; "
                      "returning empty historical data.")
            return pd.DataFrame(columns=_OUTPUT_COLUMNS)

        # Build standardised output
        df = pd.DataFrame()
        df["tournament_year"] = raw["tournament_year"].astype(int)
        df["competition"] = "World Cup"

        # Date
        if "match_date" in raw.columns:
            df["date"] = raw["match_date"].values
        elif "date" in raw.columns:
            df["date"] = raw["date"].values
        else:
            df["date"] = None

        # Stage
        df["stage"] = raw.get("stage_name", raw.get("stage", "Unknown")).values

        # Teams
        home_col = next(
            (c for c in ("home_team_name", "home_team", "team_home") if c in raw.columns),
            None,
        )
        away_col = next(
            (c for c in ("away_team_name", "away_team", "team_away") if c in raw.columns),
            None,
        )
        df["team_home"] = raw[home_col].values if home_col else "Unknown"
        df["team_away"] = raw[away_col].values if away_col else "Unknown"

        # Scores
        score_home_col = next(
            (c for c in ("home_team_score", "score_home", "home_score") if c in raw.columns),
            None,
        )
        score_away_col = next(
            (c for c in ("away_team_score", "score_away", "away_score") if c in raw.columns),
            None,
        )
        df["score_home"] = raw[score_home_col].values if score_home_col else None
        df["score_away"] = raw[score_away_col].values if score_away_col else None

        # Venue / city
        df["venue"] = raw.get("stadium_name", raw.get("venue", "Unknown")).values
        df["city"] = raw.get("city_name", raw.get("city", "Unknown")).values

        # Coordinates from config
        df["latitude"] = df["venue"].map(
            lambda v: config.VENUE_COORDS.get(v, (0, 0))[0]
        )
        df["longitude"] = df["venue"].map(
            lambda v: config.VENUE_COORDS.get(v, (0, 0))[1]
        )

        # Referee
        df["referee"] = raw.get(
            "referee_name", raw.get("referee", pd.Series(["Unknown"] * len(raw)))
        ).values

        # Source
        df["_source"] = "fjelstul"

        # Match ID
        df["match_id"] = df.apply(
            lambda r: _make_match_id(str(r["date"]), r["team_home"], r["team_away"]),
            axis=1,
        )

        self._log(f"Historical: {len(df)} matches from {_HISTORICAL_MIN_YEAR}+.")
        return df[_OUTPUT_COLUMNS]

    def _load_real_2026(self) -> pd.DataFrame:
        """Load observed 2026 results from the scraped artifact JSON.

        Only matches that were actually played are present in the artifact;
        this method never fabricates scores or fixtures. If the artifact is
        missing, an empty (correctly-typed) frame is returned so the pipeline
        degrades to "no 2026 data yet" rather than inventing matches.
        """
        if not os.path.exists(_WC2026_RESULTS_PATH):
            self._log(
                f"2026 results artifact not found at {_WC2026_RESULTS_PATH}; "
                "run `python -m backend.data.build_wc2026_results` first. "
                "Proceeding with no 2026 matches."
            )
            return pd.DataFrame(columns=_OUTPUT_COLUMNS)

        with open(_WC2026_RESULTS_PATH, encoding="utf-8") as f:
            payload = json.load(f)

        rows: list[dict] = []
        for m in payload.get("matches", []):
            venue = m["venue"]
            coords = config.VENUE_COORDS.get(venue, (0, 0))
            rows.append({
                "match_id": m["matchId"],
                "competition": m["competition"],
                "tournament_year": 2026,
                "date": m["date"],
                "stage": m["stage"],
                "team_home": m["homeTeam"],
                "team_away": m["awayTeam"],
                "score_home": m["finalScore"]["home"],
                "score_away": m["finalScore"]["away"],
                "venue": venue,
                "city": m.get("city", "Unknown"),
                "latitude": coords[0],
                "longitude": coords[1],
                "referee": "Unknown",
                "_source": m.get("source", "wc2026_results.json"),
            })

        df = pd.DataFrame(rows, columns=_OUTPUT_COLUMNS)
        self._log(f"Observed 2026: {len(df)} played matches from artifact.")
        return df
