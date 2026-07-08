"""
Match ID Resolver — Universal cross-source match identification.

Generates deterministic match IDs from the natural key (date, sorted teams,
competition) after normalising team names through country_mapping.csv.
"""

import hashlib
import os
import pandas as pd
from difflib import SequenceMatcher
from typing import Optional

_MAPPING_PATH = os.path.join(os.path.dirname(__file__), "country_mapping.csv")


class MatchIDResolver:
    """Resolves team names to canonical forms and generates match IDs."""

    def __init__(self, mapping_path: str = _MAPPING_PATH):
        self._mapping = pd.read_csv(mapping_path, encoding="utf-8")
        self._lookup: dict[str, str] = {}
        self._build_lookup()

    # ── public API ───────────────────────────────────────────────────────

    def canonical(self, name: str) -> str:
        """Return the canonical team name for any known alias."""
        key = self._normalise_key(name)
        if key in self._lookup:
            return self._lookup[key]
        # Fuzzy fallback – useful for Wikipedia edge-cases
        best, score = self._fuzzy_match(key)
        if score >= 0.80:
            self._lookup[key] = best  # cache for next time
            return best
        # Give up – return input stripped
        return name.strip()

    def generate_match_id(
        self,
        date: str,
        team_a: str,
        team_b: str,
        competition: str = "World Cup",
    ) -> str:
        """
        Deterministic match ID from natural key.

        Teams are sorted alphabetically (canonical form) so the same match
        always produces the same hash regardless of home/away ordering.
        """
        ca = self.canonical(team_a)
        cb = self.canonical(team_b)
        teams_sorted = sorted([ca, cb])
        raw = f"{date}|{teams_sorted[0]}|{teams_sorted[1]}|{competition}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def unify_dataframe(
        self,
        df: pd.DataFrame,
        team_cols: list[str],
        date_col: str = "date",
        competition_col: str = "competition",
    ) -> pd.DataFrame:
        """
        Add a deterministic ``match_id`` column to *df*.

        Parameters
        ----------
        team_cols : list[str]
            Exactly two column names containing the team names (e.g.
            ``["team_home", "team_away"]``).
        """
        df = df.copy()
        for col in team_cols:
            df[col] = df[col].apply(self.canonical)

        df["match_id"] = df.apply(
            lambda r: self.generate_match_id(
                str(r[date_col]),
                r[team_cols[0]],
                r[team_cols[1]],
                r.get(competition_col, "World Cup") if competition_col in df.columns else "World Cup",
            ),
            axis=1,
        )
        return df

    def get_iso3(self, name: str) -> Optional[str]:
        """Return ISO-3166-1 alpha-3 code for a team name."""
        canon = self.canonical(name)
        row = self._mapping.loc[
            self._mapping["canonical_name"] == canon
        ]
        if len(row):
            return row.iloc[0]["iso3"]
        return None

    # ── internals ────────────────────────────────────────────────────────

    def _normalise_key(self, s: str) -> str:
        """Lower-case, strip accents for lookup purposes."""
        import unicodedata
        s = s.strip().lower()
        # Decompose accented characters
        nfkd = unicodedata.normalize("NFKD", s)
        return "".join(c for c in nfkd if not unicodedata.combining(c))

    def _build_lookup(self):
        """Build a flat dict: every known alias → canonical_name."""
        for _, row in self._mapping.iterrows():
            canon = row["canonical_name"]
            # Every column is a possible alias
            for col in [
                "canonical_name",
                "fifa_name",
                "world_bank_name",
                "statsbomb_name",
                "betfair_name",
            ]:
                val = row.get(col)
                if pd.notna(val) and val:
                    self._lookup[self._normalise_key(str(val))] = canon
            # alt_names is semicolon-separated
            alts = row.get("alt_names", "")
            if pd.notna(alts) and alts:
                for alt in str(alts).split(";"):
                    alt = alt.strip()
                    if alt:
                        self._lookup[self._normalise_key(alt)] = canon
            # ISO3 as an alias too
            iso3 = row.get("iso3")
            if pd.notna(iso3) and iso3:
                self._lookup[self._normalise_key(str(iso3))] = canon

    def _fuzzy_match(self, key: str) -> tuple[str, float]:
        """Return (best_canonical, score) using SequenceMatcher."""
        best_canon = key
        best_score = 0.0
        for alias, canon in self._lookup.items():
            score = SequenceMatcher(None, key, alias).ratio()
            if score > best_score:
                best_score = score
                best_canon = canon
        return best_canon, best_score
