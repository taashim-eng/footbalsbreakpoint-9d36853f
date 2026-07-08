"""
Rankings Collector - Hardcoded FIFA rankings and squad values.

Provides FIFA rankings at tournament time and estimated squad market values (in Millions EUR)
for World Cup participants from 2002 to 2026.
"""

import os
import pandas as pd
from backend.data.collectors.base_collector import BaseCollector
from backend.data.match_id_resolver import MatchIDResolver
from backend import config

class RankingsCollector(BaseCollector):
    def __init__(self, match_df: pd.DataFrame = None):
        super().__init__("rankings", str(config.RAW_DIR))
        self.resolver = MatchIDResolver()
        self.match_df = match_df

    def collect(self, force: bool = False) -> pd.DataFrame:
        # We output a combined rankings + squad value dataframe or return rankings
        cache_key = "rankings_raw"
        if not force and self._is_cache_valid(cache_key):
            self._log("Returning cached rankings data.")
            return self._read_cache(cache_key)

        self._log("Generating rankings and squad values...")
        
        # Hardcoded database of FIFA rankings at tournament time for major nations
        # If a team is not in this list, we fall back to a rank based on their GDP category or average rank (e.g. 50)
        rankings_data = {
            # 2026 teams
            (2026, "USA"): 11, (2026, "Germany"): 16, (2026, "France"): 2, (2026, "England"): 4,
            (2026, "Japan"): 18, (2026, "Canada"): 49, (2026, "Netherlands"): 7, (2026, "Australia"): 23,
            (2026, "South Korea"): 22, (2026, "Belgium"): 3, (2026, "Switzerland"): 19, (2026, "Denmark"): 21,
            (2026, "Mexico"): 15, (2026, "Jamaica"): 55, (2026, "Ecuador"): 31, (2026, "Bolivia"): 84,
            (2026, "Portugal"): 6, (2026, "Iran"): 20, (2026, "Paraguay"): 56, (2026, "Panama"): 43,
            (2026, "Uruguay"): 14, (2026, "Colombia"): 12, (2026, "Indonesia"): 134, (2026, "Nigeria"): 30,
            (2026, "Cameroon"): 46, (2026, "Argentina"): 1, (2026, "Morocco"): 13, (2026, "Peru"): 32,
            (2026, "Spain"): 8, (2026, "Turkey"): 40, (2026, "New Zealand"): 104, (2026, "Chile"): 42,
            (2026, "Costa Rica"): 52, (2026, "Italy"): 9, (2026, "Austria"): 25, (2026, "Egypt"): 36,
            (2026, "Senegal"): 17, (2026, "Ghana"): 68, (2026, "Croatia"): 10, (2026, "Serbia"): 33,
            (2026, "Tunisia"): 41, (2026, "Ukraine"): 22, (2026, "Poland"): 28, (2026, "Honduras"): 78,
            (2026, "Haiti"): 86, (2026, "Cape Verde"): 65, (2026, "Uzbekistan"): 64, (2026, "Jordan"): 71,
            (2026, "Curaçao"): 90,

            # 2022 teams
            (2022, "Qatar"): 50, (2022, "Ecuador"): 44, (2022, "Senegal"): 18, (2022, "Netherlands"): 8,
            (2022, "England"): 5, (2022, "Iran"): 20, (2022, "USA"): 16, (2022, "Wales"): 19,
            (2022, "Argentina"): 3, (2022, "Saudi Arabia"): 51, (2022, "Mexico"): 13, (2022, "Poland"): 26,
            (2022, "France"): 4, (2022, "Australia"): 38, (2022, "Denmark"): 10, (2022, "Tunisia"): 30,
            (2022, "Spain"): 7, (2022, "Costa Rica"): 31, (2022, "Germany"): 11, (2022, "Japan"): 24,
            (2022, "Belgium"): 2, (2022, "Canada"): 41, (2022, "Morocco"): 22, (2022, "Croatia"): 12,
            (2022, "Brazil"): 1, (2022, "Serbia"): 21, (2022, "Switzerland"): 15, (2022, "Cameroon"): 43,
            (2022, "Portugal"): 9, (2022, "Ghana"): 61, (2022, "Uruguay"): 14, (2022, "South Korea"): 28,

            # 2018 teams
            (2018, "Russia"): 70, (2018, "Saudi Arabia"): 67, (2018, "Egypt"): 45, (2018, "Uruguay"): 14,
            (2018, "Portugal"): 4, (2018, "Spain"): 10, (2018, "Morocco"): 41, (2018, "Iran"): 37,
            (2018, "France"): 7, (2018, "Australia"): 36, (2018, "Peru"): 11, (2018, "Denmark"): 12,
            (2018, "Argentina"): 5, (2018, "Iceland"): 22, (2018, "Croatia"): 20, (2018, "Nigeria"): 48,
            (2018, "Brazil"): 2, (2018, "Switzerland"): 6, (2018, "Costa Rica"): 23, (2018, "Serbia"): 34,
            (2018, "Germany"): 1, (2018, "Mexico"): 15, (2018, "Sweden"): 24, (2018, "South Korea"): 57,
            (2018, "Belgium"): 3, (2018, "Panama"): 55, (2018, "Tunisia"): 21, (2018, "England"): 12,
            (2018, "Poland"): 8, (2018, "Senegal"): 27, (2018, "Colombia"): 16, (2018, "Japan"): 61,

            # 2014 teams
            (2014, "Brazil"): 3, (2014, "Croatia"): 18, (2014, "Mexico"): 20, (2014, "Cameroon"): 56,
            (2014, "Spain"): 1, (2014, "Netherlands"): 15, (2014, "Chile"): 14, (2014, "Australia"): 62,
            (2014, "Colombia"): 8, (2014, "Greece"): 12, (2014, "Ivory Coast"): 23, (2014, "Japan"): 46,
            (2014, "Uruguay"): 7, (2014, "Costa Rica"): 28, (2014, "England"): 10, (2014, "Italy"): 9,
            (2014, "Switzerland"): 6, (2014, "Ecuador"): 26, (2014, "France"): 17, (2014, "Honduras"): 33,
            (2014, "Argentina"): 5, (2014, "Bosnia and Herzegovina"): 21, (2014, "Iran"): 43, (2014, "Nigeria"): 44,
            (2014, "Germany"): 2, (2014, "Portugal"): 4, (2014, "Ghana"): 37, (2014, "USA"): 13,
            (2014, "Belgium"): 11, (2014, "Algeria"): 22, (2014, "Russia"): 19, (2014, "South Korea"): 57,

            # 2010 teams
            (2010, "South Africa"): 83, (2010, "Mexico"): 17, (2010, "Uruguay"): 16, (2010, "France"): 9,
            (2010, "Argentina"): 7, (2010, "Nigeria"): 21, (2010, "South Korea"): 47, (2010, "Greece"): 13,
            (2010, "England"): 8, (2010, "USA"): 14, (2010, "Algeria"): 30, (2010, "Slovenia"): 25,
            (2010, "Germany"): 6, (2010, "Australia"): 20, (2010, "Serbia"): 15, (2010, "Ghana"): 32,
            (2010, "Netherlands"): 4, (2010, "Denmark"): 36, (2010, "Japan"): 45, (2010, "Cameroon"): 19,
            (2010, "Italy"): 5, (2010, "Paraguay"): 31, (2010, "New Zealand"): 78, (2010, "Slovakia"): 34,
            (2010, "Brazil"): 1, (2010, "North Korea"): 105, (2010, "Ivory Coast"): 27, (2010, "Portugal"): 3,
            (2010, "Spain"): 2, (2010, "Switzerland"): 24, (2010, "Honduras"): 38, (2010, "Chile"): 18,

            # 2006 teams
            (2006, "Germany"): 19, (2006, "Costa Rica"): 26, (2006, "Poland"): 29, (2006, "Ecuador"): 39,
            (2006, "England"): 10, (2006, "Paraguay"): 33, (2006, "Trinidad and Tobago"): 47, (2006, "Sweden"): 16,
            (2006, "Argentina"): 9, (2006, "Ivory Coast"): 32, (2006, "Serbia"): 44, (2006, "Netherlands"): 3,
            (2006, "Mexico"): 4, (2006, "Iran"): 23, (2006, "Angola"): 57, (2006, "Portugal"): 7,
            (2006, "Italy"): 13, (2006, "Ghana"): 48, (2006, "USA"): 5, (2006, "Czechia"): 2,
            (2006, "Brazil"): 1, (2006, "Croatia"): 23, (2006, "Australia"): 42, (2006, "Japan"): 18,
            (2006, "France"): 8, (2006, "Switzerland"): 35, (2006, "South Korea"): 29, (2006, "Togo"): 61,
            (2006, "Spain"): 5, (2006, "Ukraine"): 45, (2006, "Tunisia"): 21, (2006, "Saudi Arabia"): 34,

            # 2002 teams
            (2002, "France"): 1, (2002, "Senegal"): 42, (2002, "Uruguay"): 24, (2002, "Denmark"): 20,
            (2002, "Spain"): 8, (2002, "Slovenia"): 25, (2002, "Paraguay"): 18, (2002, "South Africa"): 37,
            (2002, "Brazil"): 2, (2002, "Turkey"): 22, (2002, "China"): 50, (2002, "Costa Rica"): 29,
            (2002, "South Korea"): 40, (2002, "Poland"): 38, (2002, "USA"): 13, (2002, "Portugal"): 5,
            (2002, "Germany"): 11, (2002, "Saudi Arabia"): 34, (2002, "Ireland"): 15, (2002, "Cameroon"): 17,
            (2002, "Argentina"): 3, (2002, "Nigeria"): 27, (2002, "England"): 12, (2002, "Sweden"): 19,
            (2002, "Italy"): 6, (2002, "Ecuador"): 36, (2002, "Croatia"): 21, (2002, "Mexico"): 7,
            (2002, "Japan"): 32, (2002, "Belgium"): 23, (2002, "Russia"): 28, (2002, "Tunisia"): 31,
        }

        # Squad Market Values (Millions EUR) for teams at 2026/2022
        # For older tournaments, we can scale down based on inflation/historical ratios
        squad_values = {
            "Argentina": 900.0, "France": 1100.0, "England": 1200.0, "Brazil": 1000.0,
            "Portugal": 950.0, "Spain": 850.0, "Germany": 750.0, "Italy": 650.0,
            "Netherlands": 600.0, "Belgium": 450.0, "Uruguay": 400.0, "Croatia": 350.0,
            "Japan": 300.0, "USA": 350.0, "South Korea": 180.0, "Senegal": 250.0,
            "Morocco": 300.0, "Serbia": 220.0, "Switzerland": 200.0, "Denmark": 220.0,
            "Ukraine": 200.0, "Poland": 150.0, "Austria": 180.0, "Nigeria": 300.0,
            "Turkey": 200.0, "Colombia": 220.0, "Mexico": 150.0, "Ecuador": 180.0,
            "Canada": 150.0, "Ghana": 140.0, "Cameroon": 120.0, "Egypt": 100.0,
            "Tunisia": 60.0, "Australia": 50.0, "Jamaica": 80.0, "Cape Verde": 40.0,
            "Paraguay": 100.0, "Chile": 80.0, "Peru": 50.0, "Costa Rica": 30.0,
            "Panama": 20.0, "Honduras": 15.0, "Bolivia": 12.0, "Uzbekistan": 30.0,
            "Jordan": 15.0, "Haiti": 15.0, "Curaçao": 12.0, "Indonesia": 10.0,
            "New Zealand": 15.0, "Qatar": 15.0, "Saudi Arabia": 25.0
        }

        # Build list of all team-years in match_df to generate records
        if self.match_df is None:
            from backend.data.collectors.match_collector import MatchCollector
            self.match_df = MatchCollector().collect()

        team_years = set()
        for _, match in self.match_df.iterrows():
            team_years.add((int(match["tournament_year"]), match["team_home"]))
            team_years.add((int(match["tournament_year"]), match["team_away"]))

        records = []
        for year, team in team_years:
            canonical_team = self.resolver.canonical(team)
            
            # 1) Get FIFA ranking
            rank = rankings_data.get((year, canonical_team))
            if rank is None:
                # Fuzzy match or fallback
                # Default rank by year & group (if Group B we make it lower, group A higher)
                rank = 50
                for (ryear, rteam), rval in rankings_data.items():
                    if ryear == year and self.resolver.canonical(rteam) == canonical_team:
                        rank = rval
                        break
            
            # 2) Get Squad Value
            base_value = squad_values.get(canonical_team, 20.0)
            # Scale down for historical years (deflator proxy)
            scale = 1.0
            if year == 2022: scale = 0.9
            elif year == 2018: scale = 0.7
            elif year == 2014: scale = 0.5
            elif year == 2010: scale = 0.35
            elif year == 2006: scale = 0.25
            elif year == 2002: scale = 0.15
            squad_val = round(base_value * scale, 1)

            records.append({
                "team": canonical_team,
                "tournament_year": year,
                "fifa_ranking": rank,
                "squad_value_m_eur": squad_val,
                "_source": "rankings_collector_hardcoded"
            })

        df = pd.DataFrame(records)
        self._write_cache(df, cache_key)
        self._log(f"Generated rankings and squad values for {len(df)} team-year pairs.")
        return df
