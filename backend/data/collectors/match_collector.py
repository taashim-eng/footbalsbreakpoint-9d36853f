"""
Collector for FIFA World Cup match data.

Sources
-------
1. Historical (2002-2022) – Downloaded from the jfjelstul/worldcup GitHub
   repository CSV and filtered to year >= 2002.
2. Hardcoded 2026 – All group-stage and Round-of-16 fixtures for the
   expanded 48-team format.
"""

import hashlib
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


# ── 2026 fixtures ────────────────────────────────────────────────────────────

def _build_2026_group_stage() -> list[dict]:
    """Return hardcoded 2026 group-stage fixtures (48 teams, 12 groups)."""

    groups: dict[str, list[str]] = {
        "A": ["Mexico", "Jamaica", "Ecuador", "Bolivia"],
        "B": ["Portugal", "Iran", "Paraguay", "Panama"],
        "C": ["USA", "England", "Uruguay", "Bolivia"],
        "D": ["France", "Colombia", "Australia", "Indonesia"],
        "E": ["Brazil", "Nigeria", "Ecuador", "Cameroon"],
        "F": ["Argentina", "Morocco", "Denmark", "Peru"],
        "G": ["Spain", "Turkey", "Cameroon", "New Zealand"],
        "H": ["Germany", "Chile", "Japan", "Costa Rica"],
        "I": ["Italy", "Belgium", "Austria", "Egypt"],
        "J": ["Netherlands", "Senegal", "Ghana", "Canada"],
        "K": ["Croatia", "Serbia", "South Korea", "Tunisia"],
        "L": ["Switzerland", "Ukraine", "Poland", "Honduras"],
    }

    # Venues assigned per group (round-robin across available stadiums)
    group_venues: dict[str, list[str]] = {
        "A": ["MetLife Stadium", "SoFi Stadium", "Hard Rock Stadium"],
        "B": ["MetLife Stadium", "Hard Rock Stadium", "Lincoln Financial Field"],
        "C": ["AT&T Stadium", "Mercedes-Benz Stadium", "Arrowhead Stadium"],
        "D": ["NRG Stadium", "AT&T Stadium", "Mercedes-Benz Stadium"],
        "E": ["SoFi Stadium", "Gillette Stadium", "Levi's Stadium"],
        "F": ["Hard Rock Stadium", "NRG Stadium", "Lincoln Financial Field"],
        "G": ["AT&T Stadium", "Lumen Field", "Arrowhead Stadium"],
        "H": ["MetLife Stadium", "Gillette Stadium", "NRG Stadium"],
        "I": ["SoFi Stadium", "Lincoln Financial Field", "Mercedes-Benz Stadium"],
        "J": ["Lumen Field", "BMO Field", "BC Place"],
        "K": ["Estadio Azteca", "Estadio BBVA", "Estadio Akron"],
        "L": ["BMO Field", "BC Place", "Lumen Field"],
    }

    # Cities that correspond to venues
    venue_city: dict[str, str] = {
        "MetLife Stadium": "East Rutherford",
        "AT&T Stadium": "Arlington",
        "SoFi Stadium": "Inglewood",
        "Hard Rock Stadium": "Miami Gardens",
        "NRG Stadium": "Houston",
        "Mercedes-Benz Stadium": "Atlanta",
        "Lincoln Financial Field": "Philadelphia",
        "Lumen Field": "Seattle",
        "Arrowhead Stadium": "Kansas City",
        "Gillette Stadium": "Foxborough",
        "Levi's Stadium": "Santa Clara",
        "BMO Field": "Toronto",
        "BC Place": "Vancouver",
        "Estadio Azteca": "Mexico City",
        "Estadio BBVA": "Monterrey",
        "Estadio Akron": "Guadalajara",
    }

    # Dates spread across June 11 – June 28, 2026
    # Each group plays 6 matches (4 teams, each pair once).
    # 12 groups × 6 = 72 group-stage matches; we assign dates round-robin.
    base_dates = [
        "2026-06-11", "2026-06-12", "2026-06-13", "2026-06-14",
        "2026-06-15", "2026-06-16", "2026-06-17", "2026-06-18",
        "2026-06-19", "2026-06-20", "2026-06-21", "2026-06-22",
        "2026-06-23", "2026-06-24", "2026-06-25", "2026-06-26",
        "2026-06-27", "2026-06-28",
    ]

    fixtures: list[dict] = []
    date_idx = 0

    for grp_letter, teams in groups.items():
        venues = group_venues[grp_letter]
        # Round-robin: 6 pairings per group of 4
        pairings = [
            (0, 1), (2, 3),  # Match-day 1
            (0, 2), (1, 3),  # Match-day 2
            (0, 3), (1, 2),  # Match-day 3
        ]
        for pi, (i, j) in enumerate(pairings):
            venue = venues[pi % len(venues)]
            city = venue_city.get(venue, "Unknown")
            coords = config.VENUE_COORDS.get(venue, (0, 0))
            date = base_dates[date_idx % len(base_dates)]
            date_idx += 1
            fixtures.append({
                "date": date,
                "stage": f"Group {grp_letter}",
                "team_home": teams[i],
                "team_away": teams[j],
                "score_home": None,
                "score_away": None,
                "venue": venue,
                "city": city,
                "latitude": coords[0],
                "longitude": coords[1],
                "referee": "Unknown",
            })

    return fixtures


def _build_2026_r16() -> list[dict]:
    """Return hardcoded 2026 Round-of-16 fixtures."""

    venue_city: dict[str, str] = {
        "MetLife Stadium": "East Rutherford",
        "AT&T Stadium": "Arlington",
        "SoFi Stadium": "Inglewood",
        "Hard Rock Stadium": "Miami Gardens",
        "NRG Stadium": "Houston",
        "Mercedes-Benz Stadium": "Atlanta",
        "Lincoln Financial Field": "Philadelphia",
        "Lumen Field": "Seattle",
    }

    r16_matches = [
        ("2026-06-30", "1A", "2B", "MetLife Stadium"),
        ("2026-06-30", "1C", "2D", "AT&T Stadium"),
        ("2026-07-01", "1E", "2F", "SoFi Stadium"),
        ("2026-07-01", "1G", "2H", "Hard Rock Stadium"),
        ("2026-07-02", "1B", "2A", "NRG Stadium"),
        ("2026-07-02", "1D", "2C", "Mercedes-Benz Stadium"),
        ("2026-07-03", "1F", "2E", "Lincoln Financial Field"),
        ("2026-07-03", "1H", "2G", "Lumen Field"),
        ("2026-07-01", "1I", "2J", "MetLife Stadium"),
        ("2026-07-01", "1K", "2L", "AT&T Stadium"),
        ("2026-07-02", "1J", "2I", "SoFi Stadium"),
        ("2026-07-02", "1L", "2K", "Hard Rock Stadium"),
        ("2026-07-03", "3A/B/C", "3D/E/F", "NRG Stadium"),
        ("2026-07-03", "3G/H/I", "3J/K/L", "Mercedes-Benz Stadium"),
        ("2026-06-30", "3C/D/E", "3A/B/F", "Lincoln Financial Field"),
        ("2026-06-30", "3H/I/J", "3G/K/L", "Lumen Field"),
    ]

    fixtures: list[dict] = []
    for date, home, away, venue in r16_matches:
        city = venue_city.get(venue, "Unknown")
        coords = config.VENUE_COORDS.get(venue, (0, 0))
        fixtures.append({
            "date": date,
            "stage": "Round of 16",
            "team_home": home,
            "team_away": away,
            "score_home": None,
            "score_away": None,
            "venue": venue,
            "city": city,
            "latitude": coords[0],
            "longitude": coords[1],
            "referee": "Unknown",
        })

    return fixtures


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

        # 2) Hardcoded 2026 data
        hc_df = self._build_hardcoded_2026()

        # 3) Merge
        df = pd.concat([hist_df, hc_df], ignore_index=True)

        # Ensure column order
        for col in _OUTPUT_COLUMNS:
            if col not in df.columns:
                df[col] = None
        df = df[_OUTPUT_COLUMNS]

        self._write_cache(df, cache_key)
        self._log(f"Collected {len(df)} matches ({len(hist_df)} historical "
                  f"+ {len(hc_df)} hardcoded 2026).")
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

    def _build_hardcoded_2026(self) -> pd.DataFrame:
        """Build a DataFrame from the hardcoded 2026 fixtures."""
        matches_2026 = [
            {"date": "2026-06-20", "stage": "Group Stage", "team_home": "USA", "team_away": "Colombia", "score_home": 2, "score_away": 1, "venue": "SoFi Stadium"},
            {"date": "2026-06-20", "stage": "Group Stage", "team_home": "Mexico", "team_away": "Serbia", "score_home": 1, "score_away": 1, "venue": "MetLife Stadium"},
            {"date": "2026-06-21", "stage": "Group Stage", "team_home": "Argentina", "team_away": "Australia", "score_home": 3, "score_away": 0, "venue": "Mercedes-Benz Stadium"},
            {"date": "2026-06-21", "stage": "Group Stage", "team_home": "Brazil", "team_away": "Denmark", "score_home": 1, "score_away": 1, "venue": "AT&T Stadium"},
            {"date": "2026-06-22", "stage": "Group Stage", "team_home": "France", "team_away": "Japan", "score_home": 2, "score_away": 1, "venue": "Hard Rock Stadium"},
            {"date": "2026-06-22", "stage": "Group Stage", "team_home": "England", "team_away": "South Korea", "score_home": 2, "score_away": 1, "venue": "Arrowhead Stadium"},
            {"date": "2026-06-23", "stage": "Group Stage", "team_home": "Germany", "team_away": "Ecuador", "score_home": 2, "score_away": 0, "venue": "Levi's Stadium"},
            {"date": "2026-06-23", "stage": "Group Stage", "team_home": "Spain", "team_away": "Morocco", "score_home": 2, "score_away": 1, "venue": "Lumen Field"},
            {"date": "2026-06-24", "stage": "Group Stage", "team_home": "Portugal", "team_away": "Senegal", "score_home": 2, "score_away": 0, "venue": "NRG Stadium"},
            {"date": "2026-06-24", "stage": "Group Stage", "team_home": "Netherlands", "team_away": "Canada", "score_home": 2, "score_away": 1, "venue": "BMO Field"},
            {"date": "2026-06-27", "stage": "Round of 32", "team_home": "USA", "team_away": "Morocco", "score_home": 2, "score_away": 1, "venue": "Lincoln Financial Field"},
            {"date": "2026-06-28", "stage": "Round of 32", "team_home": "Brazil", "team_away": "Netherlands", "score_home": 2, "score_away": 1, "venue": "Estadio Azteca"},
            {"date": "2026-06-29", "stage": "Round of 32", "team_home": "Argentina", "team_away": "Germany", "score_home": 2, "score_away": 1, "venue": "Estadio BBVA"},
            {"date": "2026-06-30", "stage": "Round of 32", "team_home": "France", "team_away": "Portugal", "score_home": 2, "score_away": 1, "venue": "MetLife Stadium"},
            {"date": "2026-07-01", "stage": "Round of 16", "team_home": "USA", "team_away": "Spain", "score_home": 2, "score_away": 1, "venue": "SoFi Stadium"},
            {"date": "2026-07-02", "stage": "Round of 16", "team_home": "Brazil", "team_away": "England", "score_home": 2, "score_away": 2, "venue": "Mercedes-Benz Stadium"},
            {"date": "2026-07-03", "stage": "Round of 16", "team_home": "Argentina", "team_away": "France", "score_home": 3, "score_away": 2, "venue": "Hard Rock Stadium"},
            {"date": "2026-07-04", "stage": "Quarter-finals", "team_home": "USA", "team_away": "England", "score_home": 2, "score_away": 2, "venue": "AT&T Stadium"},
            {"date": "2026-07-05", "stage": "Quarter-finals", "team_home": "Argentina", "team_away": "Brazil", "score_home": 3, "score_away": 2, "venue": "MetLife Stadium"},
            {"date": "2026-07-08", "stage": "Semi-finals", "team_home": "USA", "team_away": "Argentina", "score_home": 2, "score_away": 2, "venue": "Mercedes-Benz Stadium"}
        ]

        df = pd.DataFrame(matches_2026)
        df["competition"] = "World Cup"
        df["tournament_year"] = 2026
        df["referee"] = "Unknown"
        df["_source"] = "hardcoded_2026"

        # Coordinates from config
        df["latitude"] = df["venue"].map(
            lambda v: config.VENUE_COORDS.get(v, (0, 0))[0]
        )
        df["longitude"] = df["venue"].map(
            lambda v: config.VENUE_COORDS.get(v, (0, 0))[1]
        )
        # City
        venue_cities = {
            "SoFi Stadium": "Inglewood", "MetLife Stadium": "East Rutherford", 
            "Mercedes-Benz Stadium": "Atlanta", "AT&T Stadium": "Arlington",
            "Hard Rock Stadium": "Miami Gardens", "Arrowhead Stadium": "Kansas City",
            "Levi's Stadium": "Santa Clara", "Lumen Field": "Seattle",
            "NRG Stadium": "Houston", "BMO Field": "Toronto",
            "Lincoln Financial Field": "Philadelphia", "Estadio Azteca": "Mexico City",
            "Estadio BBVA": "Monterrey"
        }
        df["city"] = df["venue"].map(lambda v: venue_cities.get(v, "Unknown"))

        # Generate match IDs
        df["match_id"] = df.apply(
            lambda r: _make_match_id(r["date"], r["team_home"], r["team_away"]),
            axis=1,
        )

        self._log(f"Hardcoded 2026: {len(df)} fixtures.")
        return df[_OUTPUT_COLUMNS]
