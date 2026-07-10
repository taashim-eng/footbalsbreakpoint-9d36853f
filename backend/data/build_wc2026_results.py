"""
build_wc2026_results.py — One-time scrape artifact for the 2026 FIFA World Cup.

The 2026 tournament is in progress. This module holds the real, observed
match results that had actually been *played* as of the scrape date, and
emits them to ``backend/data/raw/wc2026_results.json`` for downstream use by
the match collector and the dashboard exporter.

Only completed matches are included. Fixtures that had not yet kicked off at
scrape time (quarter-finals onward, 2026-07-09+) are intentionally omitted —
we do not emit results that do not exist.

Provenance
----------
- Match schedule, scores and venues: ESPN 2026 FIFA World Cup daily schedule
  pages (https://www.espn.com/soccer/schedule/_/date/YYYYMMDD/league/fifa.world)
  cross-checked against FIFA.com match centre and Wikipedia group articles.
- Group letters (A-L): Wikipedia "2026 FIFA World Cup" group tables.
- Scrape date: 2026-07-08 (through the Round of 16, completed 2026-07-07).

Every value here is an observed final result. No scores, dates, odds, or
per-minute data are synthesised. Kickoff clock times were not captured, so
dates are recorded as calendar dates (YYYY-MM-DD) per ISO 8601.

Run ``python -m backend.data.build_wc2026_results`` to regenerate the JSON.
"""

import json
import os

SCRAPE_DATE = "2026-07-08"
COMPETITION = "FIFA World Cup 2026"
SOURCE = "ESPN 2026 FIFA World Cup schedule + FIFA.com match centre, scraped 2026-07-08"

# FIFA three-letter country codes for the 48 participating nations, used to
# build stable, human-readable match IDs.
TEAM_CODES = {
    "Mexico": "MEX", "South Africa": "RSA", "South Korea": "KOR", "Czechia": "CZE",
    "Canada": "CAN", "Bosnia-Herzegovina": "BIH", "Qatar": "QAT", "Switzerland": "SUI",
    "Brazil": "BRA", "Morocco": "MAR", "Haiti": "HAI", "Scotland": "SCO",
    "United States": "USA", "Paraguay": "PAR", "Australia": "AUS", "Türkiye": "TUR",
    "Germany": "GER", "Curaçao": "CUW", "Ivory Coast": "CIV", "Ecuador": "ECU",
    "Netherlands": "NED", "Japan": "JPN", "Sweden": "SWE", "Tunisia": "TUN",
    "Belgium": "BEL", "Egypt": "EGY", "Iran": "IRN", "New Zealand": "NZL",
    "Spain": "ESP", "Cape Verde": "CPV", "Saudi Arabia": "KSA", "Uruguay": "URU",
    "France": "FRA", "Senegal": "SEN", "Iraq": "IRQ", "Norway": "NOR",
    "Argentina": "ARG", "Algeria": "ALG", "Austria": "AUT", "Jordan": "JOR",
    "Portugal": "POR", "Congo DR": "COD", "Uzbekistan": "UZB", "Colombia": "COL",
    "England": "ENG", "Croatia": "CRO", "Ghana": "GHA", "Panama": "PAN",
}

# City lookup keyed by venue (observed from the match reports).
VENUE_CITY = {
    "Estadio Banorte": "Mexico City", "Estadio Akron": "Guadalajara",
    "Estadio BBVA": "Guadalupe", "BMO Field": "Toronto", "BC Place": "Vancouver",
    "SoFi Stadium": "Inglewood", "Levi's Stadium": "Santa Clara",
    "MetLife Stadium": "East Rutherford", "Gillette Stadium": "Foxborough",
    "NRG Stadium": "Houston", "AT&T Stadium": "Arlington",
    "Lincoln Financial Field": "Philadelphia", "Mercedes-Benz Stadium": "Atlanta",
    "Lumen Field": "Seattle", "Hard Rock Stadium": "Miami Gardens",
    "GEHA Field at Arrowhead Stadium": "Kansas City",
}

# Observed results. Each tuple: (date, stage, home, away, score_home, score_away,
# venue, penalties-or-None). Penalties are (home, away) shootout goals when a
# knockout was decided on penalties; None otherwise.
_RESULTS = [
    # ── Group stage — Matchday 1 (Jun 11-17) ──────────────────────────────
    ("2026-06-11", "Group A", "Mexico", "South Africa", 2, 0, "Estadio Banorte", None),
    ("2026-06-11", "Group A", "South Korea", "Czechia", 2, 1, "Estadio Akron", None),
    ("2026-06-12", "Group B", "Canada", "Bosnia-Herzegovina", 1, 1, "BMO Field", None),
    ("2026-06-12", "Group D", "United States", "Paraguay", 4, 1, "SoFi Stadium", None),
    ("2026-06-13", "Group B", "Qatar", "Switzerland", 1, 1, "Levi's Stadium", None),
    ("2026-06-13", "Group C", "Brazil", "Morocco", 1, 1, "MetLife Stadium", None),
    ("2026-06-13", "Group C", "Haiti", "Scotland", 0, 1, "Gillette Stadium", None),
    ("2026-06-13", "Group D", "Australia", "Türkiye", 2, 0, "BC Place", None),
    ("2026-06-14", "Group E", "Germany", "Curaçao", 7, 1, "NRG Stadium", None),
    ("2026-06-14", "Group F", "Netherlands", "Japan", 2, 2, "AT&T Stadium", None),
    ("2026-06-14", "Group E", "Ivory Coast", "Ecuador", 1, 0, "Lincoln Financial Field", None),
    ("2026-06-14", "Group F", "Sweden", "Tunisia", 5, 1, "Estadio BBVA", None),
    ("2026-06-15", "Group H", "Spain", "Cape Verde", 0, 0, "Mercedes-Benz Stadium", None),
    ("2026-06-15", "Group G", "Belgium", "Egypt", 1, 1, "Lumen Field", None),
    ("2026-06-15", "Group H", "Uruguay", "Saudi Arabia", 1, 1, "Hard Rock Stadium", None),
    ("2026-06-15", "Group G", "Iran", "New Zealand", 2, 2, "SoFi Stadium", None),
    ("2026-06-16", "Group I", "France", "Senegal", 3, 1, "MetLife Stadium", None),
    ("2026-06-16", "Group I", "Norway", "Iraq", 4, 1, "Gillette Stadium", None),
    ("2026-06-16", "Group J", "Argentina", "Algeria", 3, 0, "GEHA Field at Arrowhead Stadium", None),
    ("2026-06-17", "Group J", "Austria", "Jordan", 3, 1, "Levi's Stadium", None),
    ("2026-06-17", "Group K", "Portugal", "Congo DR", 1, 1, "NRG Stadium", None),
    ("2026-06-17", "Group L", "England", "Croatia", 4, 2, "AT&T Stadium", None),
    ("2026-06-17", "Group L", "Ghana", "Panama", 1, 0, "BMO Field", None),
    ("2026-06-17", "Group K", "Colombia", "Uzbekistan", 3, 1, "Estadio Banorte", None),
    # ── Group stage — Matchday 2 (Jun 18-23) ──────────────────────────────
    ("2026-06-18", "Group A", "Czechia", "South Africa", 1, 1, "Mercedes-Benz Stadium", None),
    ("2026-06-18", "Group B", "Switzerland", "Bosnia-Herzegovina", 4, 1, "SoFi Stadium", None),
    ("2026-06-18", "Group B", "Canada", "Qatar", 6, 0, "BC Place", None),
    ("2026-06-18", "Group A", "Mexico", "South Korea", 1, 0, "Estadio Akron", None),
    ("2026-06-19", "Group D", "United States", "Australia", 2, 0, "Lumen Field", None),
    ("2026-06-19", "Group C", "Scotland", "Morocco", 0, 1, "Gillette Stadium", None),
    ("2026-06-19", "Group C", "Brazil", "Haiti", 3, 0, "Lincoln Financial Field", None),
    ("2026-06-19", "Group D", "Türkiye", "Paraguay", 0, 1, "Levi's Stadium", None),
    ("2026-06-20", "Group F", "Netherlands", "Sweden", 5, 1, "NRG Stadium", None),
    ("2026-06-20", "Group E", "Germany", "Ivory Coast", 2, 1, "BMO Field", None),
    ("2026-06-20", "Group E", "Ecuador", "Curaçao", 0, 0, "GEHA Field at Arrowhead Stadium", None),
    ("2026-06-21", "Group F", "Japan", "Tunisia", 4, 0, "Estadio BBVA", None),
    ("2026-06-21", "Group H", "Spain", "Saudi Arabia", 4, 0, "Mercedes-Benz Stadium", None),
    ("2026-06-21", "Group G", "Belgium", "Iran", 0, 0, "SoFi Stadium", None),
    ("2026-06-21", "Group H", "Uruguay", "Cape Verde", 2, 2, "Hard Rock Stadium", None),
    ("2026-06-21", "Group G", "Egypt", "New Zealand", 3, 1, "BC Place", None),
    ("2026-06-22", "Group J", "Argentina", "Austria", 2, 0, "AT&T Stadium", None),
    ("2026-06-22", "Group I", "France", "Iraq", 3, 0, "Lincoln Financial Field", None),
    ("2026-06-22", "Group I", "Norway", "Senegal", 3, 2, "MetLife Stadium", None),
    ("2026-06-22", "Group J", "Algeria", "Jordan", 2, 1, "Levi's Stadium", None),
    ("2026-06-23", "Group K", "Portugal", "Uzbekistan", 5, 0, "NRG Stadium", None),
    ("2026-06-23", "Group L", "England", "Ghana", 0, 0, "Gillette Stadium", None),
    ("2026-06-23", "Group L", "Croatia", "Panama", 1, 0, "BMO Field", None),
    ("2026-06-23", "Group K", "Colombia", "Congo DR", 1, 0, "Estadio Akron", None),
    # ── Group stage — Matchday 3 (Jun 24-27) ──────────────────────────────
    ("2026-06-24", "Group B", "Bosnia-Herzegovina", "Qatar", 3, 1, "Lumen Field", None),
    ("2026-06-24", "Group B", "Switzerland", "Canada", 2, 1, "BC Place", None),
    ("2026-06-24", "Group C", "Morocco", "Haiti", 4, 2, "Mercedes-Benz Stadium", None),
    ("2026-06-24", "Group C", "Brazil", "Scotland", 3, 0, "Hard Rock Stadium", None),
    ("2026-06-24", "Group A", "Mexico", "Czechia", 3, 0, "Estadio Banorte", None),
    ("2026-06-24", "Group A", "South Africa", "South Korea", 1, 0, "Estadio BBVA", None),
    ("2026-06-25", "Group E", "Curaçao", "Ivory Coast", 0, 2, "Lincoln Financial Field", None),
    ("2026-06-25", "Group E", "Ecuador", "Germany", 2, 1, "MetLife Stadium", None),
    ("2026-06-25", "Group F", "Japan", "Sweden", 1, 1, "AT&T Stadium", None),
    ("2026-06-25", "Group F", "Tunisia", "Netherlands", 1, 3, "GEHA Field at Arrowhead Stadium", None),
    ("2026-06-25", "Group D", "Paraguay", "Australia", 0, 0, "Levi's Stadium", None),
    ("2026-06-25", "Group D", "Türkiye", "United States", 3, 2, "SoFi Stadium", None),
    ("2026-06-26", "Group I", "Norway", "France", 1, 4, "Gillette Stadium", None),
    ("2026-06-26", "Group I", "Iraq", "Senegal", 5, 0, "BMO Field", None),
    ("2026-06-26", "Group H", "Cape Verde", "Saudi Arabia", 0, 0, "NRG Stadium", None),
    ("2026-06-26", "Group H", "Uruguay", "Spain", 0, 1, "Estadio Akron", None),
    ("2026-06-26", "Group G", "Iran", "Egypt", 1, 1, "Lumen Field", None),
    ("2026-06-26", "Group G", "New Zealand", "Belgium", 1, 5, "BC Place", None),
    ("2026-06-27", "Group L", "Ghana", "Croatia", 2, 1, "Lincoln Financial Field", None),
    ("2026-06-27", "Group L", "Panama", "England", 0, 2, "MetLife Stadium", None),
    ("2026-06-27", "Group K", "Portugal", "Colombia", 0, 0, "Hard Rock Stadium", None),
    ("2026-06-27", "Group K", "Uzbekistan", "Congo DR", 3, 1, "Mercedes-Benz Stadium", None),
    ("2026-06-27", "Group J", "Austria", "Algeria", 3, 3, "GEHA Field at Arrowhead Stadium", None),
    ("2026-06-27", "Group J", "Argentina", "Jordan", 3, 1, "AT&T Stadium", None),
    # ── Round of 32 (Jun 28 - Jul 3) ──────────────────────────────────────
    ("2026-06-28", "Round of 32", "South Africa", "Canada", 0, 1, "SoFi Stadium", None),
    ("2026-06-29", "Round of 32", "Japan", "Brazil", 1, 2, "NRG Stadium", None),
    ("2026-06-29", "Round of 32", "Paraguay", "Germany", 1, 1, "Gillette Stadium", (4, 3)),
    ("2026-06-29", "Round of 32", "Morocco", "Netherlands", 1, 1, "Estadio BBVA", (3, 2)),
    ("2026-06-30", "Round of 32", "Ivory Coast", "Norway", 1, 2, "AT&T Stadium", None),
    ("2026-06-30", "Round of 32", "Sweden", "France", 0, 3, "MetLife Stadium", None),
    ("2026-06-30", "Round of 32", "Ecuador", "Mexico", 0, 2, "Estadio Banorte", None),
    ("2026-07-01", "Round of 32", "Congo DR", "England", 1, 2, "Mercedes-Benz Stadium", None),
    ("2026-07-01", "Round of 32", "Senegal", "Belgium", 2, 3, "Lumen Field", None),
    ("2026-07-01", "Round of 32", "Bosnia-Herzegovina", "United States", 0, 2, "Levi's Stadium", None),
    ("2026-07-02", "Round of 32", "Austria", "Spain", 0, 3, "SoFi Stadium", None),
    ("2026-07-02", "Round of 32", "Croatia", "Portugal", 1, 2, "BMO Field", None),
    ("2026-07-02", "Round of 32", "Algeria", "Switzerland", 0, 2, "BC Place", None),
    ("2026-07-03", "Round of 32", "Egypt", "Australia", 1, 1, "AT&T Stadium", (4, 2)),
    ("2026-07-03", "Round of 32", "Cape Verde", "Argentina", 2, 3, "Hard Rock Stadium", None),
    ("2026-07-03", "Round of 32", "Ghana", "Colombia", 0, 1, "GEHA Field at Arrowhead Stadium", None),
    # ── Round of 16 (Jul 4-7) ─────────────────────────────────────────────
    ("2026-07-04", "Round of 16", "Morocco", "Canada", 3, 0, "NRG Stadium", None),
    ("2026-07-04", "Round of 16", "France", "Paraguay", 1, 0, "Lincoln Financial Field", None),
    ("2026-07-05", "Round of 16", "Brazil", "Norway", 1, 2, "MetLife Stadium", None),
    ("2026-07-05", "Round of 16", "Mexico", "England", 2, 3, "Estadio Banorte", None),
    ("2026-07-06", "Round of 16", "Portugal", "Spain", 0, 1, "AT&T Stadium", None),
    ("2026-07-06", "Round of 16", "United States", "Belgium", 1, 4, "Lumen Field", None),
    ("2026-07-07", "Round of 16", "Argentina", "Egypt", 3, 2, "Mercedes-Benz Stadium", None),
    ("2026-07-07", "Round of 16", "Switzerland", "Colombia", 0, 0, "BC Place", (4, 3)),
]


def _match_id(home: str, away: str) -> str:
    """Stable ID: WC2026-{homeCode}-{awayCode} (spec-defined format)."""
    return f"WC2026-{TEAM_CODES[home]}-{TEAM_CODES[away]}"


def build_records() -> list[dict]:
    """Return the observed 2026 matches as structured, sourced records."""
    records: list[dict] = []
    seen_ids: set[str] = set()
    for date, stage, home, away, sh, sa, venue, pens in _RESULTS:
        mid = _match_id(home, away)
        if mid in seen_ids:
            raise ValueError(f"Duplicate matchId {mid} ({home} vs {away})")
        seen_ids.add(mid)
        rec = {
            "matchId": mid,
            "date": date,  # calendar date; kickoff clock time not captured
            "competition": COMPETITION,
            "stage": stage,
            "homeTeam": home,
            "awayTeam": away,
            "venue": venue,
            "city": VENUE_CITY.get(venue, "Unknown"),
            "finalScore": {"home": sh, "away": sa},
            "source": SOURCE,
        }
        if pens is not None:
            rec["penalties"] = {"home": pens[0], "away": pens[1]}
        records.append(rec)
    return records


def main() -> None:
    records = build_records()
    out = {
        "competition": COMPETITION,
        "scrapeDate": SCRAPE_DATE,
        "source": SOURCE,
        "note": (
            "Observed completed matches only (group stage through Round of 16). "
            "Quarter-finals onward had not been played at scrape time and are omitted."
        ),
        "matches": records,
    }
    out_path = os.path.join(os.path.dirname(__file__), "raw", "wc2026_results.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(records)} observed 2026 matches to {out_path}")


if __name__ == "__main__":
    main()
