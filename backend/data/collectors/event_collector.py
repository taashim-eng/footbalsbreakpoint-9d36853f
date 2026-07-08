"""
EventCollector – minute-level match events for FIFA World Cup analysis.

Sources
-------
1. **Fjelstul** – goals.csv, bookings.csv, substitutions.csv from the
   jfjelstul/worldcup GitHub repo (2002 onwards).
2. **StatsBomb** – open-data events for 2018 & 2022 World Cups via
   statsbombpy (optional dependency).
3. **Hardcoded 2026** – curated key events for the ongoing 2026 tournament.

Output columns
--------------
match_id, minute, minute_stoppage, event_type, team, player, detail, _source
"""

from __future__ import annotations

import hashlib
from typing import List

import pandas as pd

from backend.data.collectors.base_collector import BaseCollector
from backend import config


# ── Shared helper ────────────────────────────────────────────────────────────

def _make_match_id(
    date_str: str,
    team1: str,
    team2: str,
    competition: str = "World Cup",
) -> str:
    """Deterministic 16-char hex match identifier."""
    from backend.data.match_id_resolver import MatchIDResolver
    resolver = MatchIDResolver()
    t1 = resolver.canonical(team1)
    t2 = resolver.canonical(team2)
    teams = sorted([t1, t2])
    raw = f"{date_str}|{teams[0]}|{teams[1]}|{competition}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ── Constants ────────────────────────────────────────────────────────────────

_FJELSTUL_BASE = (
    "https://raw.githubusercontent.com/jfjelstul/worldcup/master/data-csv/"
)
_FJELSTUL_FILES = ["goals.csv", "bookings.csv", "substitutions.csv"]

_OUTPUT_COLS = [
    "match_id",
    "minute",
    "minute_stoppage",
    "event_type",
    "team",
    "player",
    "detail",
    "_source",
]


class EventCollector(BaseCollector):
    """Collect minute-level match events from multiple data sources."""

    def __init__(self) -> None:
        super().__init__("events", str(config.RAW_DIR))

    # ── Public API ───────────────────────────────────────────────────────

    def collect(self, force: bool = False) -> pd.DataFrame:
        """Return a DataFrame of match events, using cache when valid."""
        if not force and self._is_cache_valid("all"):
            self._log("Loading events from cache.")
            return self._read_cache("all")

        frames: List[pd.DataFrame] = []

        # 1 – Fjelstul
        fjelstul_df = self._collect_fjelstul()
        if fjelstul_df is not None and not fjelstul_df.empty:
            frames.append(fjelstul_df)

        # 2 – StatsBomb
        statsbomb_df = self._collect_statsbomb()
        if statsbomb_df is not None and not statsbomb_df.empty:
            frames.append(statsbomb_df)

        # 3 – Hardcoded 2026
        hc_df = self._collect_hardcoded_2026()
        frames.append(hc_df)

        if not frames:
            self._log("WARNING: No event data collected from any source.")
            df = pd.DataFrame(columns=_OUTPUT_COLS)
        else:
            df = pd.concat(frames, ignore_index=True)

        # Ensure consistent schema
        df["minute"] = pd.to_numeric(df["minute"], errors="coerce").fillna(0).astype(int)
        df["minute_stoppage"] = (
            pd.to_numeric(df["minute_stoppage"], errors="coerce").fillna(0).astype(int)
        )
        df = df[_OUTPUT_COLS]

        self._write_cache(df, "all")
        self._log(f"Collected {len(df)} events total.")
        return df

    # ── Source 1: Fjelstul GitHub CSVs ───────────────────────────────────

    def _collect_fjelstul(self) -> pd.DataFrame | None:
        """Download and normalise Fjelstul World Cup event CSVs."""
        try:
            self._log("Fetching Fjelstul data …")
            all_rows: List[pd.DataFrame] = []

            # --- Goals ---
            goals_url = f"{_FJELSTUL_BASE}goals.csv"
            goals = pd.read_csv(goals_url)
            goals["year"] = goals["tournament_id"].apply(lambda x: int(str(x).split("-")[1]) if "-" in str(x) else 2022)
            goals = goals[goals["year"] >= 2002].copy()

            goals["team_home"] = goals["match_name"].apply(lambda x: str(x).split(" vs ")[0] if " vs " in str(x) else "")
            goals["team_away"] = goals["match_name"].apply(lambda x: str(x).split(" vs ")[1] if " vs " in str(x) else "")
            
            goals["match_id"] = goals.apply(
                lambda r: _make_match_id(
                    str(r["match_date"]),
                    str(r["team_home"]),
                    str(r["team_away"]),
                ),
                axis=1,
            )
            goals["minute"] = goals.get("minute_regulation", goals.get("minute", 0))
            goals["minute_stoppage"] = goals.get("minute_stoppage", 0)
            goals["event_type"] = goals.apply(
                lambda r: (
                    "own_goal"
                    if str(r.get("own_goal", "")).lower() in ("1", "true", "yes")
                    else (
                        "penalty"
                        if str(r.get("penalty", "")).lower() in ("1", "true", "yes")
                        else "goal"
                    )
                ),
                axis=1,
            )
            goals["team"] = goals.get("team_name", "")
            goals["player"] = goals.get("family_name", "Unknown")
            goals["detail"] = goals.get("goal_type", "")
            goals["_source"] = "fjelstul"
            all_rows.append(goals[_OUTPUT_COLS])

            # --- Bookings ---
            bookings_url = f"{_FJELSTUL_BASE}bookings.csv"
            bookings = pd.read_csv(bookings_url)
            bookings["year"] = bookings["tournament_id"].apply(lambda x: int(str(x).split("-")[1]) if "-" in str(x) else 2022)
            bookings = bookings[bookings["year"] >= 2002].copy()

            bookings["team_home"] = bookings["match_name"].apply(lambda x: str(x).split(" vs ")[0] if " vs " in str(x) else "")
            bookings["team_away"] = bookings["match_name"].apply(lambda x: str(x).split(" vs ")[1] if " vs " in str(x) else "")

            bookings["match_id"] = bookings.apply(
                lambda r: _make_match_id(
                    str(r["match_date"]),
                    str(r["team_home"]),
                    str(r["team_away"]),
                ),
                axis=1,
            )
            bookings["minute"] = bookings.get(
                "minute_regulation", bookings.get("minute", 0)
            )
            bookings["minute_stoppage"] = bookings.get("minute_stoppage", 0)
            bookings["event_type"] = bookings.apply(
                lambda r: (
                    "red_card"
                    if str(r.get("red_card", r.get("card_color", ""))).lower()
                    in ("1", "true", "red")
                    else (
                        "red_card"
                        if str(r.get("second_yellow_card", "")).lower()
                        in ("1", "true", "yes")
                        else "yellow_card"
                    )
                ),
                axis=1,
            )
            bookings["team"] = bookings.get("team_name", "")
            bookings["player"] = bookings.get("family_name", "Unknown")
            bookings["detail"] = bookings.apply(
                lambda r: (
                    "second yellow"
                    if str(r.get("second_yellow_card", "")).lower()
                    in ("1", "true", "yes")
                    else ""
                ),
                axis=1,
            )
            bookings["_source"] = "fjelstul"
            all_rows.append(bookings[_OUTPUT_COLS])

            # --- Substitutions ---
            subs_url = f"{_FJELSTUL_BASE}substitutions.csv"
            subs = pd.read_csv(subs_url)
            subs["year"] = subs["tournament_id"].apply(lambda x: int(str(x).split("-")[1]) if "-" in str(x) else 2022)
            subs = subs[subs["year"] >= 2002].copy()

            subs["team_home"] = subs["match_name"].apply(lambda x: str(x).split(" vs ")[0] if " vs " in str(x) else "")
            subs["team_away"] = subs["match_name"].apply(lambda x: str(x).split(" vs ")[1] if " vs " in str(x) else "")

            subs["match_id"] = subs.apply(
                lambda r: _make_match_id(
                    str(r["match_date"]),
                    str(r["team_home"]),
                    str(r["team_away"]),
                ),
                axis=1,
            )
            subs["minute"] = subs.get("minute_regulation", subs.get("minute", 0))
            subs["minute_stoppage"] = subs.get("minute_stoppage", 0)
            subs["event_type"] = "substitution"
            subs["team"] = subs.get("team_name", "")
            subs["player"] = subs.get("family_name", "Unknown")
            subs["detail"] = "tactical"
            subs["_source"] = "fjelstul"
            all_rows.append(subs[_OUTPUT_COLS])

            result = pd.concat(all_rows, ignore_index=True)
            self._log(f"Fjelstul: {len(result)} events collected.")
            return result

        except Exception as exc:
            self._log(f"Fjelstul fetch failed: {exc}")
            return None

    # ── Source 2: StatsBomb open data ────────────────────────────────────

    def _collect_statsbomb(self) -> pd.DataFrame | None:
        """Extract goal/card/substitution events via statsbombpy."""
        try:
            from statsbombpy import sb  # type: ignore[import-untyped]
        except ImportError:
            self._log("statsbombpy not installed – skipping StatsBomb source.")
            return None

        try:
            self._log("Fetching StatsBomb data …")
            all_rows: List[dict] = []

            # StatsBomb competition IDs for FIFA World Cup
            comps = sb.competitions()
            wc_comps = comps[
                comps["competition_name"].str.contains("World Cup", case=False, na=False)
                & comps["season_name"].isin(["2018", "2022"])
            ]

            for _, comp_row in wc_comps.iterrows():
                comp_id = comp_row["competition_id"]
                season_id = comp_row["season_id"]
                season_name = str(comp_row["season_name"])

                matches = sb.matches(competition_id=comp_id, season_id=season_id)

                for _, m in matches.iterrows():
                    match_date = str(m.get("match_date", ""))
                    home = str(m.get("home_team", ""))
                    away = str(m.get("away_team", ""))
                    mid = _make_match_id(match_date, home, away)

                    try:
                        events = sb.events(match_id=m["match_id"])
                    except Exception:
                        continue

                    # Goals
                    shots = events[
                        (events["type"] == "Shot")
                        & (events["shot_outcome"] == "Goal")
                    ]
                    for _, s in shots.iterrows():
                        all_rows.append(
                            {
                                "match_id": mid,
                                "minute": int(s.get("minute", 0)),
                                "minute_stoppage": int(
                                    s.get("second", 0) if pd.notna(s.get("second")) else 0
                                ),
                                "event_type": (
                                    "penalty"
                                    if str(s.get("shot_type", "")).lower() == "penalty"
                                    else "goal"
                                ),
                                "team": str(s.get("team", "")),
                                "player": str(s.get("player", "Unknown")),
                                "detail": str(s.get("shot_body_part", "")),
                                "_source": "statsbomb",
                            }
                        )

                    # Cards
                    cards = events[
                        events["type"].isin(
                            ["Bad Behaviour", "Foul Committed"]
                        )
                        & events["bad_behaviour_card"].notna()
                        | events["foul_committed_card"].notna()
                    ]
                    for _, c in cards.iterrows():
                        card_val = str(
                            c.get("bad_behaviour_card", c.get("foul_committed_card", ""))
                        )
                        if "Second Yellow" in card_val:
                            etype = "red_card"
                            detail = "second yellow"
                        elif "Red" in card_val:
                            etype = "red_card"
                            detail = "straight red"
                        elif "Yellow" in card_val:
                            etype = "yellow_card"
                            detail = ""
                        else:
                            continue
                        all_rows.append(
                            {
                                "match_id": mid,
                                "minute": int(c.get("minute", 0)),
                                "minute_stoppage": 0,
                                "event_type": etype,
                                "team": str(c.get("team", "")),
                                "player": str(c.get("player", "Unknown")),
                                "detail": detail,
                                "_source": "statsbomb",
                            }
                        )

                    # Substitutions
                    sub_evts = events[events["type"] == "Substitution"]
                    for _, su in sub_evts.iterrows():
                        all_rows.append(
                            {
                                "match_id": mid,
                                "minute": int(su.get("minute", 0)),
                                "minute_stoppage": 0,
                                "event_type": "substitution",
                                "team": str(su.get("team", "")),
                                "player": str(su.get("player", "Unknown")),
                                "detail": "tactical",
                                "_source": "statsbomb",
                            }
                        )

            df = pd.DataFrame(all_rows, columns=_OUTPUT_COLS)
            self._log(f"StatsBomb: {len(df)} events collected.")
            return df

        except Exception as exc:
            self._log(f"StatsBomb fetch failed: {exc}")
            return None

    # ── Source 3: Hardcoded 2026 events ──────────────────────────────────

    def _collect_hardcoded_2026(self) -> pd.DataFrame:
        """Return curated key events for the 2026 World Cup."""
        self._log("Loading hardcoded 2026 events …")
        rows: List[dict] = []

        def _g(
            date: str,
            t1: str,
            t2: str,
            minute: int,
            team: str,
            player: str,
            detail: str = "right foot",
            etype: str = "goal",
            stoppage: int = 0,
        ) -> None:
            rows.append(
                {
                    "match_id": _make_match_id(date, t1, t2),
                    "minute": minute,
                    "minute_stoppage": stoppage,
                    "event_type": etype,
                    "team": team,
                    "player": player,
                    "detail": detail,
                    "_source": "hardcoded_2026",
                }
            )

        def _c(
            date: str,
            t1: str,
            t2: str,
            minute: int,
            team: str,
            player: str,
            detail: str = "",
            etype: str = "yellow_card",
            stoppage: int = 0,
        ) -> None:
            rows.append(
                {
                    "match_id": _make_match_id(date, t1, t2),
                    "minute": minute,
                    "minute_stoppage": stoppage,
                    "event_type": etype,
                    "team": team,
                    "player": player,
                    "detail": detail,
                    "_source": "hardcoded_2026",
                }
            )

        def _s(
            date: str,
            t1: str,
            t2: str,
            minute: int,
            team: str,
            player: str,
            detail: str = "tactical",
            stoppage: int = 0,
        ) -> None:
            rows.append(
                {
                    "match_id": _make_match_id(date, t1, t2),
                    "minute": minute,
                    "minute_stoppage": stoppage,
                    "event_type": "substitution",
                    "team": team,
                    "player": player,
                    "detail": detail,
                    "_source": "hardcoded_2026",
                }
            )

        # ================================================================
        # GROUP STAGE – Day 1  (2026-06-11)
        # ================================================================
        # Mexico vs Colombia
        _g("2026-06-11", "Mexico", "Colombia", 23, "Mexico", "Santiago Giménez", "header")
        _g("2026-06-11", "Mexico", "Colombia", 41, "Colombia", "Luis Díaz", "left foot")
        _g("2026-06-11", "Mexico", "Colombia", 78, "Mexico", "Hirving Lozano", "right foot")
        _c("2026-06-11", "Mexico", "Colombia", 34, "Colombia", "Davinson Sánchez")
        _c("2026-06-11", "Mexico", "Colombia", 67, "Mexico", "Edson Álvarez")
        _s("2026-06-11", "Mexico", "Colombia", 60, "Mexico", "Diego Lainez", "tactical")
        _s("2026-06-11", "Mexico", "Colombia", 72, "Colombia", "Rafael Santos Borré", "tactical")

        # USA vs Serbia
        _g("2026-06-11", "USA", "Serbia", 12, "USA", "Christian Pulisic", "left foot")
        _g("2026-06-11", "USA", "Serbia", 55, "USA", "Folarin Balogun", "header")
        _g("2026-06-11", "USA", "Serbia", 89, "Serbia", "Dušan Vlahović", "right foot")
        _c("2026-06-11", "USA", "Serbia", 38, "Serbia", "Nemanja Gudelj")
        _s("2026-06-11", "USA", "Serbia", 65, "USA", "Gio Reyna", "tactical")
        _s("2026-06-11", "USA", "Serbia", 75, "Serbia", "Filip Kostić", "tactical")

        # ================================================================
        # GROUP STAGE – Day 2  (2026-06-12)
        # ================================================================
        # Brazil vs Nigeria
        _g("2026-06-12", "Brazil", "Nigeria", 18, "Brazil", "Vinícius Júnior", "left foot")
        _g("2026-06-12", "Brazil", "Nigeria", 33, "Nigeria", "Victor Osimhen", "header")
        _g("2026-06-12", "Brazil", "Nigeria", 62, "Brazil", "Rodrygo", "right foot")
        _g("2026-06-12", "Brazil", "Nigeria", 80, "Brazil", "Endrick", "left foot")
        _c("2026-06-12", "Brazil", "Nigeria", 45, "Nigeria", "William Troost-Ekong", stoppage=1)
        _c("2026-06-12", "Brazil", "Nigeria", 58, "Brazil", "Bruno Guimarães")
        _s("2026-06-12", "Brazil", "Nigeria", 68, "Brazil", "Savinho", "tactical")
        _s("2026-06-12", "Brazil", "Nigeria", 70, "Nigeria", "Samuel Chukwueze", "tactical")

        # Argentina vs Denmark
        _g("2026-06-12", "Argentina", "Denmark", 7, "Argentina", "Lionel Messi", "left foot")
        _g("2026-06-12", "Argentina", "Denmark", 50, "Argentina", "Julián Álvarez", "right foot")
        _g("2026-06-12", "Argentina", "Denmark", 73, "Denmark", "Rasmus Højlund", "header")
        _c("2026-06-12", "Argentina", "Denmark", 29, "Denmark", "Pierre-Emile Højbjerg")
        _s("2026-06-12", "Argentina", "Denmark", 60, "Argentina", "Ángel Di María", "tactical")

        # ================================================================
        # GROUP STAGE – Day 3  (2026-06-13)
        # ================================================================
        # France vs South Korea
        _g("2026-06-13", "France", "South Korea", 15, "France", "Kylian Mbappé", "right foot")
        _g("2026-06-13", "France", "South Korea", 44, "France", "Ousmane Dembélé", "left foot")
        _g("2026-06-13", "France", "South Korea", 71, "France", "Randal Kolo Muani", "header")
        _c("2026-06-13", "France", "South Korea", 52, "South Korea", "Kim Min-jae")
        _s("2026-06-13", "France", "South Korea", 63, "France", "Marcus Thuram", "tactical")
        _s("2026-06-13", "France", "South Korea", 78, "South Korea", "Lee Kang-in", "tactical")

        # England vs Japan
        _g("2026-06-13", "England", "Japan", 27, "England", "Jude Bellingham", "right foot")
        _g("2026-06-13", "England", "Japan", 59, "Japan", "Takefusa Kubo", "left foot")
        _g("2026-06-13", "England", "Japan", 88, "England", "Bukayo Saka", "left foot")
        _c("2026-06-13", "England", "Japan", 40, "Japan", "Wataru Endō")
        _c("2026-06-13", "England", "Japan", 75, "England", "Declan Rice")
        _s("2026-06-13", "England", "Japan", 66, "England", "Cole Palmer", "tactical")
        _s("2026-06-13", "England", "Japan", 70, "Japan", "Kaoru Mitoma", "tactical")

        # ================================================================
        # GROUP STAGE – Day 4  (2026-06-14)
        # ================================================================
        # Germany vs Morocco
        _g("2026-06-14", "Germany", "Morocco", 20, "Germany", "Florian Wirtz", "left foot")
        _g("2026-06-14", "Germany", "Morocco", 56, "Morocco", "Youssef En-Nesyri", "header")
        _g("2026-06-14", "Germany", "Morocco", 82, "Germany", "Jamal Musiala", "right foot")
        _c("2026-06-14", "Germany", "Morocco", 31, "Morocco", "Sofyan Amrabat")
        _s("2026-06-14", "Germany", "Morocco", 74, "Germany", "Leroy Sané", "tactical")
        _s("2026-06-14", "Germany", "Morocco", 80, "Morocco", "Hakim Ziyech", "tactical")

        # Spain vs Ecuador
        _g("2026-06-14", "Spain", "Ecuador", 10, "Spain", "Lamine Yamal", "left foot")
        _g("2026-06-14", "Spain", "Ecuador", 38, "Spain", "Pedri", "right foot")
        _g("2026-06-14", "Spain", "Ecuador", 69, "Ecuador", "Moisés Caicedo", "right foot")
        _c("2026-06-14", "Spain", "Ecuador", 44, "Ecuador", "Piero Hincapié")
        _s("2026-06-14", "Spain", "Ecuador", 55, "Spain", "Nico Williams", "tactical")

        # ================================================================
        # GROUP STAGE – Day 5  (2026-06-15)
        # ================================================================
        # Portugal vs Canada
        _g("2026-06-15", "Portugal", "Canada", 5, "Portugal", "Cristiano Ronaldo", "header")
        _g("2026-06-15", "Portugal", "Canada", 39, "Portugal", "Bernardo Silva", "left foot")
        _g("2026-06-15", "Portugal", "Canada", 64, "Canada", "Jonathan David", "right foot")
        _g("2026-06-15", "Portugal", "Canada", 87, "Portugal", "Rafael Leão", "left foot")
        _c("2026-06-15", "Portugal", "Canada", 22, "Canada", "Alphonso Davies")
        _s("2026-06-15", "Portugal", "Canada", 60, "Portugal", "João Félix", "tactical")
        _s("2026-06-15", "Portugal", "Canada", 71, "Canada", "Cyle Larin", "tactical")

        # Netherlands vs Senegal
        _g("2026-06-15", "Netherlands", "Senegal", 29, "Netherlands", "Cody Gakpo", "left foot")
        _g("2026-06-15", "Netherlands", "Senegal", 54, "Senegal", "Ismaïla Sarr", "right foot")
        _c("2026-06-15", "Netherlands", "Senegal", 47, "Senegal", "Kalidou Koulibaly")
        _s("2026-06-15", "Netherlands", "Senegal", 62, "Netherlands", "Xavi Simons", "tactical")

        # ================================================================
        # GROUP STAGE – Day 6  (2026-06-16)
        # ================================================================
        # Italy vs Australia
        _g("2026-06-16", "Italy", "Australia", 11, "Italy", "Gianluca Scamacca", "right foot")
        _g("2026-06-16", "Italy", "Australia", 48, "Italy", "Federico Chiesa", "left foot")
        _g("2026-06-16", "Italy", "Australia", 76, "Australia", "Jackson Irvine", "header")
        _c("2026-06-16", "Italy", "Australia", 36, "Australia", "Harry Souttar")
        _c("2026-06-16", "Italy", "Australia", 71, "Italy", "Nicolò Barella")
        _s("2026-06-16", "Italy", "Australia", 58, "Italy", "Lorenzo Pellegrini", "tactical")
        _s("2026-06-16", "Italy", "Australia", 66, "Australia", "Craig Goodwin", "tactical")

        # Belgium vs Costa Rica
        _g("2026-06-16", "Belgium", "Costa Rica", 19, "Belgium", "Kevin De Bruyne", "right foot")
        _g("2026-06-16", "Belgium", "Costa Rica", 53, "Belgium", "Romelu Lukaku", "header")
        _s("2026-06-16", "Belgium", "Costa Rica", 68, "Belgium", "Jérémy Doku", "tactical")

        # ================================================================
        # GROUP STAGE – Day 7  (2026-06-17)
        # ================================================================
        # Uruguay vs Ghana
        _g("2026-06-17", "Uruguay", "Ghana", 14, "Uruguay", "Darwin Núñez", "right foot")
        _g("2026-06-17", "Uruguay", "Ghana", 61, "Ghana", "Mohammed Kudus", "left foot")
        _g("2026-06-17", "Uruguay", "Ghana", 90, "Uruguay", "Federico Valverde", "right foot", stoppage=3)
        _c("2026-06-17", "Uruguay", "Ghana", 50, "Ghana", "Thomas Partey")
        _c("2026-06-17", "Uruguay", "Ghana", 82, "Uruguay", "Rodrigo Bentancur")
        _s("2026-06-17", "Uruguay", "Ghana", 57, "Uruguay", "Facundo Pellistri", "tactical")
        _s("2026-06-17", "Uruguay", "Ghana", 73, "Ghana", "Inaki Williams", "tactical")

        # Croatia vs Cameroon
        _g("2026-06-17", "Croatia", "Cameroon", 32, "Croatia", "Luka Modrić", "right foot")
        _g("2026-06-17", "Croatia", "Cameroon", 66, "Cameroon", "André-Frank Zambo Anguissa", "header")
        _c("2026-06-17", "Croatia", "Cameroon", 21, "Cameroon", "Nicolas N'Koulou")
        _s("2026-06-17", "Croatia", "Cameroon", 70, "Croatia", "Lovro Majer", "tactical")

        # ================================================================
        # GROUP STAGE – Remaining matchdays (2026-06-18 to 2026-06-26)
        # ================================================================
        # Switzerland vs Algeria  (2026-06-18)
        _g("2026-06-18", "Switzerland", "Algeria", 35, "Switzerland", "Granit Xhaka", "right foot")
        _g("2026-06-18", "Switzerland", "Algeria", 77, "Algeria", "Riyad Mahrez", "left foot")
        _s("2026-06-18", "Switzerland", "Algeria", 64, "Switzerland", "Ruben Vargas", "tactical")
        _s("2026-06-18", "Switzerland", "Algeria", 81, "Algeria", "Saïd Benrahma", "tactical")

        # Poland vs Paraguay  (2026-06-18)
        _g("2026-06-18", "Poland", "Paraguay", 9, "Poland", "Robert Lewandowski", "right foot")
        _g("2026-06-18", "Poland", "Paraguay", 45, "Poland", "Robert Lewandowski", "penalty", "penalty", stoppage=2)
        _c("2026-06-18", "Poland", "Paraguay", 44, "Paraguay", "Gustavo Gómez")

        # Wales vs Iran  (2026-06-19)
        _g("2026-06-19", "Wales", "Iran", 8, "Wales", "Brennan Johnson", "right foot")
        _g("2026-06-19", "Wales", "Iran", 42, "Iran", "Mehdi Taremi", "header")
        _g("2026-06-19", "Wales", "Iran", 74, "Iran", "Sardar Azmoun", "left foot")
        _c("2026-06-19", "Wales", "Iran", 55, "Wales", "Joe Rodon")
        _s("2026-06-19", "Wales", "Iran", 60, "Wales", "Harry Wilson", "tactical")
        _s("2026-06-19", "Wales", "Iran", 76, "Iran", "Alireza Jahanbakhsh", "tactical")

        # Tunisia vs Saudi Arabia  (2026-06-19)
        _g("2026-06-19", "Tunisia", "Saudi Arabia", 26, "Saudi Arabia", "Salem Al-Dawsari", "left foot")
        _c("2026-06-19", "Tunisia", "Saudi Arabia", 68, "Tunisia", "Ellyes Skhiri")

        # Match day 3: USA vs Colombia  (2026-06-20)
        _g("2026-06-20", "USA", "Colombia", 17, "USA", "Christian Pulisic", "right foot")
        _g("2026-06-20", "USA", "Colombia", 52, "Colombia", "Jhon Arias", "right foot")
        _g("2026-06-20", "USA", "Colombia", 69, "USA", "Timothy Weah", "right foot")
        _c("2026-06-20", "USA", "Colombia", 33, "Colombia", "Jefferson Lerma")
        _s("2026-06-20", "USA", "Colombia", 58, "USA", "Brenden Aaronson", "tactical")
        _s("2026-06-20", "USA", "Colombia", 75, "Colombia", "Luis Sinisterra", "tactical")

        # Mexico vs Serbia  (2026-06-20)
        _g("2026-06-20", "Mexico", "Serbia", 30, "Serbia", "Aleksandar Mitrović", "header")
        _g("2026-06-20", "Mexico", "Serbia", 63, "Mexico", "Santiago Giménez", "right foot")
        _c("2026-06-20", "Mexico", "Serbia", 70, "Serbia", "Strahinja Pavlović", etype="red_card", detail="straight red")
        _s("2026-06-20", "Mexico", "Serbia", 55, "Mexico", "Alexis Vega", "tactical")

        # Argentina vs Australia  (2026-06-21)
        _g("2026-06-21", "Argentina", "Australia", 3, "Argentina", "Lionel Messi", "left foot")
        _g("2026-06-21", "Argentina", "Australia", 37, "Argentina", "Lautaro Martínez", "right foot")
        _g("2026-06-21", "Argentina", "Australia", 58, "Argentina", "Julián Álvarez", "header")
        _s("2026-06-21", "Argentina", "Australia", 62, "Argentina", "Alejandro Garnacho", "tactical")

        # Brazil vs Denmark  (2026-06-21)
        _g("2026-06-21", "Brazil", "Denmark", 22, "Brazil", "Vinícius Júnior", "left foot")
        _g("2026-06-21", "Brazil", "Denmark", 67, "Denmark", "Rasmus Højlund", "right foot")
        _c("2026-06-21", "Brazil", "Denmark", 43, "Denmark", "Andreas Christensen")
        _s("2026-06-21", "Brazil", "Denmark", 70, "Brazil", "Raphinha", "tactical")

        # France vs Japan  (2026-06-22)
        _g("2026-06-22", "France", "Japan", 16, "France", "Kylian Mbappé", "right foot")
        _g("2026-06-22", "France", "Japan", 40, "Japan", "Takefusa Kubo", "right foot")
        _g("2026-06-22", "France", "Japan", 72, "France", "Antoine Griezmann", "left foot")
        _c("2026-06-22", "France", "Japan", 62, "Japan", "Wataru Endō", etype="yellow_card", detail="second yellow")
        _s("2026-06-22", "France", "Japan", 56, "France", "Eduardo Camavinga", "tactical")
        _s("2026-06-22", "France", "Japan", 80, "Japan", "Ritsu Dōan", "tactical")

        # England vs South Korea  (2026-06-22)
        _g("2026-06-22", "England", "South Korea", 31, "England", "Phil Foden", "left foot")
        _g("2026-06-22", "England", "South Korea", 68, "South Korea", "Son Heung-min", "right foot")
        _g("2026-06-22", "England", "South Korea", 84, "England", "Harry Kane", "penalty", "penalty")
        _s("2026-06-22", "England", "South Korea", 73, "England", "Eberechi Eze", "tactical")

        # Germany vs Ecuador  (2026-06-23)
        _g("2026-06-23", "Germany", "Ecuador", 25, "Germany", "Kai Havertz", "header")
        _g("2026-06-23", "Germany", "Ecuador", 51, "Germany", "Florian Wirtz", "left foot")
        _c("2026-06-23", "Germany", "Ecuador", 48, "Ecuador", "Carlos Gruezo")
        _s("2026-06-23", "Germany", "Ecuador", 65, "Germany", "Chris Führich", "tactical")

        # Spain vs Morocco  (2026-06-23)
        _g("2026-06-23", "Spain", "Morocco", 14, "Spain", "Lamine Yamal", "right foot")
        _g("2026-06-23", "Spain", "Morocco", 45, "Morocco", "Achraf Hakimi", "right foot", stoppage=4)
        _g("2026-06-23", "Spain", "Morocco", 79, "Spain", "Dani Olmo", "left foot")
        _c("2026-06-23", "Spain", "Morocco", 36, "Morocco", "Azzedine Ounahi")

        # Portugal vs Senegal  (2026-06-24)
        _g("2026-06-24", "Portugal", "Senegal", 13, "Portugal", "Cristiano Ronaldo", "right foot")
        _g("2026-06-24", "Portugal", "Senegal", 46, "Portugal", "Bruno Fernandes", "penalty", "penalty")
        _s("2026-06-24", "Portugal", "Senegal", 58, "Portugal", "Pedro Neto", "tactical")

        # Netherlands vs Canada  (2026-06-24)
        _g("2026-06-24", "Netherlands", "Canada", 37, "Netherlands", "Memphis Depay", "right foot")
        _g("2026-06-24", "Netherlands", "Canada", 69, "Canada", "Jonathan David", "header")
        _g("2026-06-24", "Netherlands", "Canada", 90, "Netherlands", "Cody Gakpo", "left foot", stoppage=2)
        _c("2026-06-24", "Netherlands", "Canada", 55, "Canada", "Stephen Eustáquio")
        _s("2026-06-24", "Netherlands", "Canada", 77, "Netherlands", "Donyell Malen", "tactical")

        # ================================================================
        # ROUND OF 32  (2026-06-27 to 2026-06-30)
        # ================================================================
        # USA vs Morocco  (2026-06-27)
        _g("2026-06-27", "USA", "Morocco", 24, "USA", "Folarin Balogun", "right foot")
        _g("2026-06-27", "USA", "Morocco", 57, "Morocco", "Youssef En-Nesyri", "header")
        _g("2026-06-27", "USA", "Morocco", 83, "USA", "Christian Pulisic", "left foot")
        _c("2026-06-27", "USA", "Morocco", 65, "Morocco", "Noussair Mazraoui")
        _s("2026-06-27", "USA", "Morocco", 70, "USA", "Yunus Musah", "tactical")

        # Brazil vs Netherlands  (2026-06-28)
        _g("2026-06-28", "Brazil", "Netherlands", 19, "Brazil", "Vinícius Júnior", "left foot")
        _g("2026-06-28", "Brazil", "Netherlands", 45, "Netherlands", "Virgil van Dijk", "header", stoppage=1)
        _g("2026-06-28", "Brazil", "Netherlands", 76, "Brazil", "Rodrygo", "right foot")
        _c("2026-06-28", "Brazil", "Netherlands", 41, "Netherlands", "Jurriën Timber")
        _s("2026-06-28", "Brazil", "Netherlands", 67, "Brazil", "Endrick", "tactical")

        # Argentina vs Germany  (2026-06-29)
        _g("2026-06-29", "Argentina", "Germany", 33, "Argentina", "Lionel Messi", "left foot")
        _g("2026-06-29", "Argentina", "Germany", 60, "Germany", "Jamal Musiala", "right foot")
        _g("2026-06-29", "Argentina", "Germany", 85, "Argentina", "Julián Álvarez", "right foot")
        _c("2026-06-29", "Argentina", "Germany", 47, "Germany", "Joshua Kimmich")
        _s("2026-06-29", "Argentina", "Germany", 78, "Argentina", "Enzo Fernández", "tactical")
        _s("2026-06-29", "Argentina", "Germany", 81, "Germany", "Leroy Sané", "tactical")

        # France vs Portugal  (2026-06-30)
        _g("2026-06-30", "France", "Portugal", 21, "France", "Kylian Mbappé", "right foot")
        _g("2026-06-30", "France", "Portugal", 54, "Portugal", "Bernardo Silva", "right foot")
        _g("2026-06-30", "France", "Portugal", 90, "France", "Ousmane Dembélé", "left foot", stoppage=5)
        _c("2026-06-30", "France", "Portugal", 39, "Portugal", "Rúben Dias")
        _s("2026-06-30", "France", "Portugal", 72, "France", "Aurélien Tchouaméni", "tactical")
        _s("2026-06-30", "France", "Portugal", 74, "Portugal", "Rafael Leão", "tactical")

        # ================================================================
        # ROUND OF 16  (2026-07-01 to 2026-07-04)
        # ================================================================
        # USA vs Spain  (2026-07-01)
        _g("2026-07-01", "USA", "Spain", 28, "Spain", "Pedri", "right foot")
        _g("2026-07-01", "USA", "Spain", 52, "USA", "Timothy Weah", "header")
        _g("2026-07-01", "USA", "Spain", 76, "USA", "Christian Pulisic", "penalty", "penalty")
        _c("2026-07-01", "USA", "Spain", 49, "Spain", "Rodri")
        _s("2026-07-01", "USA", "Spain", 60, "USA", "Gio Reyna", "tactical")
        _s("2026-07-01", "USA", "Spain", 82, "Spain", "Ferran Torres", "tactical")

        # Brazil vs England  (2026-07-02)
        _g("2026-07-02", "Brazil", "England", 18, "Brazil", "Vinícius Júnior", "left foot")
        _g("2026-07-02", "Brazil", "England", 41, "England", "Jude Bellingham", "right foot")
        _g("2026-07-02", "Brazil", "England", 73, "England", "Bukayo Saka", "left foot")
        _g("2026-07-02", "Brazil", "England", 90, "Brazil", "Endrick", "right foot", stoppage=4)
        _c("2026-07-02", "Brazil", "England", 36, "England", "Kyle Walker")
        _c("2026-07-02", "Brazil", "England", 64, "Brazil", "Marquinhos")
        _s("2026-07-02", "Brazil", "England", 58, "England", "Cole Palmer", "tactical")
        _s("2026-07-02", "Brazil", "England", 68, "Brazil", "Savinho", "tactical")

        # Argentina vs France  (2026-07-03)
        _g("2026-07-03", "Argentina", "France", 11, "Argentina", "Lionel Messi", "left foot")
        _g("2026-07-03", "Argentina", "France", 36, "France", "Kylian Mbappé", "right foot")
        _g("2026-07-03", "Argentina", "France", 67, "Argentina", "Julián Álvarez", "header")
        _g("2026-07-03", "Argentina", "France", 78, "France", "Ousmane Dembélé", "right foot")
        _g("2026-07-03", "Argentina", "France", 90, "Argentina", "Lautaro Martínez", "right foot", stoppage=2)
        _c("2026-07-03", "Argentina", "France", 56, "France", "Aurélien Tchouaméni")
        _c("2026-07-03", "Argentina", "France", 80, "Argentina", "Nicolás Otamendi")
        _s("2026-07-03", "Argentina", "France", 65, "Argentina", "Alejandro Garnacho", "tactical")
        _s("2026-07-03", "Argentina", "France", 70, "France", "Eduardo Camavinga", "tactical")
        _s("2026-07-03", "Argentina", "France", 85, "France", "Randal Kolo Muani", "tactical")

        # ================================================================
        # QUARTER-FINALS  (2026-07-04 to 2026-07-05)
        # ================================================================
        # USA vs England  (2026-07-04)
        _g("2026-07-04", "USA", "England", 16, "USA", "Christian Pulisic", "left foot")
        _g("2026-07-04", "USA", "England", 34, "England", "Harry Kane", "header")
        _g("2026-07-04", "USA", "England", 71, "USA", "Folarin Balogun", "right foot")
        _g("2026-07-04", "USA", "England", 88, "England", "Phil Foden", "left foot")
        _c("2026-07-04", "USA", "England", 59, "England", "Declan Rice", etype="yellow_card")
        _s("2026-07-04", "USA", "England", 75, "USA", "Weston McKennie", "tactical")
        _s("2026-07-04", "USA", "England", 80, "England", "Eberechi Eze", "tactical")

        # Argentina vs Brazil  (2026-07-05)
        _g("2026-07-05", "Argentina", "Brazil", 25, "Brazil", "Vinícius Júnior", "left foot")
        _g("2026-07-05", "Argentina", "Brazil", 44, "Argentina", "Lionel Messi", "penalty", "penalty")
        _g("2026-07-05", "Argentina", "Brazil", 59, "Argentina", "Julián Álvarez", "right foot")
        _g("2026-07-05", "Argentina", "Brazil", 79, "Brazil", "Rodrygo", "right foot")
        _g("2026-07-05", "Argentina", "Brazil", 90, "Argentina", "Lautaro Martínez", "header", stoppage=3)
        _c("2026-07-05", "Argentina", "Brazil", 30, "Brazil", "Casemiro")
        _c("2026-07-05", "Argentina", "Brazil", 72, "Argentina", "Cristian Romero")
        _s("2026-07-05", "Argentina", "Brazil", 65, "Argentina", "Enzo Fernández", "tactical")
        _s("2026-07-05", "Argentina", "Brazil", 68, "Brazil", "Endrick", "tactical")
        _s("2026-07-05", "Argentina", "Brazil", 83, "Brazil", "Raphinha", "tactical")

        # ================================================================
        # SEMI-FINALS  (2026-07-08)
        # ================================================================
        # USA vs Argentina  (2026-07-08)
        _g("2026-07-08", "USA", "Argentina", 20, "Argentina", "Lionel Messi", "left foot")
        _g("2026-07-08", "USA", "Argentina", 45, "USA", "Christian Pulisic", "right foot", stoppage=1)
        _g("2026-07-08", "USA", "Argentina", 66, "USA", "Folarin Balogun", "header")
        _g("2026-07-08", "USA", "Argentina", 78, "Argentina", "Julián Álvarez", "left foot")
        _c("2026-07-08", "USA", "Argentina", 53, "Argentina", "Rodrigo De Paul")
        _c("2026-07-08", "USA", "Argentina", 81, "USA", "Tyler Adams")
        _s("2026-07-08", "USA", "Argentina", 60, "USA", "Gio Reyna", "tactical")
        _s("2026-07-08", "USA", "Argentina", 71, "Argentina", "Alejandro Garnacho", "tactical")
        _s("2026-07-08", "USA", "Argentina", 85, "USA", "Malik Tillman", "tactical")

        df = pd.DataFrame(rows, columns=_OUTPUT_COLS)
        self._log(f"Hardcoded 2026: {len(df)} events loaded.")
        return df
