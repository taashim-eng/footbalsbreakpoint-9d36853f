"""
Feature Engineering - Constructs features for statistical and ML models.

Reads SQLite tables, joins GDP, rankings, weather, and betting data,
classifies nations into Group A/B, computes time-window performance indicators,
and outputs a unified analysis Parquet dataset.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from backend import config
from backend.data.data_access import DataAccess
from backend.data.match_id_resolver import MatchIDResolver

class FeatureEngineer:
    def __init__(self):
        self.db = DataAccess()
        self.resolver = MatchIDResolver()

    def engineer_features(self) -> pd.DataFrame:
        print("Starting feature engineering...")
        
        matches = self.db.get_matches()
        gdp = self.db.get_gdp()
        weather = self.db.get_weather()
        rankings = self.db.get_rankings()
        betting = self.db.get_betting()
        
        # Build team classification: GDP and flags mapping
        # Classify Group A (above median) vs Group B (below median) per tournament year
        gdp_years = []
        for year in matches["tournament_year"].unique():
            matches_yr = matches[matches["tournament_year"] == year]
            teams_yr = set(matches_yr["team_home"].unique()) | set(matches_yr["team_away"].unique())
            
            # Map teams to ISO3 and match GDP
            gdp_records = []
            for team in teams_yr:
                iso3 = self.resolver.get_iso3(team)
                # find closest year in gdp table
                team_gdp = gdp[(gdp["country_iso3"] == iso3)]
                gdp_val = 15000.0 # Default fallback
                if len(team_gdp):
                    # Find closest year
                    team_gdp = team_gdp.copy()
                    team_gdp["year_diff"] = (team_gdp["year"] - year).abs()
                    gdp_val = team_gdp.sort_values("year_diff").iloc[0]["gdp_per_capita_ppp"]
                
                gdp_records.append({"team": team, "gdp": gdp_val})
            
            gdp_df_yr = pd.DataFrame(gdp_records)
            median_gdp = gdp_df_yr["gdp"].median()
            gdp_df_yr["gdp_group"] = gdp_df_yr["gdp"].apply(lambda g: "A" if g >= median_gdp else "B")
            gdp_df_yr["tournament_year"] = year
            gdp_years.append(gdp_df_yr)
            
        gdp_mapping = pd.concat(gdp_years, ignore_index=True)
        
        # Merge classifications into matches
        # Home
        matches = matches.merge(
            gdp_mapping, 
            left_on=["team_home", "tournament_year"], 
            right_on=["team", "tournament_year"], 
            how="left"
        ).rename(columns={"gdp": "gdp_home", "gdp_group": "gdp_group_home"}).drop(columns=["team"], errors="ignore")
        
        # Away
        matches = matches.merge(
            gdp_mapping, 
            left_on=["team_away", "tournament_year"], 
            right_on=["team", "tournament_year"], 
            how="left"
        ).rename(columns={"gdp": "gdp_away", "gdp_group": "gdp_group_away"}).drop(columns=["team"], errors="ignore")

        # Merge Rankings
        matches = matches.merge(
            rankings[["team", "tournament_year", "fifa_ranking", "squad_value_m_eur"]],
            left_on=["team_home", "tournament_year"],
            right_on=["team", "tournament_year"],
            how="left"
        ).rename(columns={"fifa_ranking": "fifa_rank_home", "squad_value_m_eur": "squad_value_home_m"}).drop(columns=["team"])
        
        matches = matches.merge(
            rankings[["team", "tournament_year", "fifa_ranking", "squad_value_m_eur"]],
            left_on=["team_away", "tournament_year"],
            right_on=["team", "tournament_year"],
            how="left"
        ).rename(columns={"fifa_ranking": "fifa_rank_away", "squad_value_m_eur": "squad_value_away_m"}).drop(columns=["team"])

        # Merge Weather
        matches = matches.merge(weather, on="match_id", how="left", suffixes=("", "_weather"))
        
        # Merge Pre-Match Betting
        matches = matches.merge(betting, on="match_id", how="left")

        # Fill missing values
        matches["fifa_rank_home"] = matches["fifa_rank_home"].fillna(50).astype(int)
        matches["fifa_rank_away"] = matches["fifa_rank_away"].fillna(50).astype(int)
        matches["squad_value_home_m"] = matches["squad_value_home_m"].fillna(50.0)
        matches["squad_value_away_m"] = matches["squad_value_away_m"].fillna(50.0)
        matches["temperature_c"] = matches["temperature_c"].fillna(22.0)
        matches["humidity_pct"] = matches["humidity_pct"].fillna(55.0)
        matches["wbgt_estimate"] = matches["wbgt_estimate"].fillna(20.0)
        matches["break_likely"] = matches["break_likely"].fillna(0).astype(int)

        # Set Era
        def get_era(year):
            if year in config.ERA_A: return "A"
            if year in config.ERA_B: return "B"
            return "C"
        matches["era"] = matches["tournament_year"].apply(get_era)

        # ── Group B Perspective metrics ──────────────────────────────────────────
        # Since the hypothesis targets Group B (lower GDP) nations, we construct 
        # features showing whether a Group B nation was leading at the break, and 
        # the goals conceded post-break from Group B's perspective.
        
        # Pull event statistics to find:
        # - Score at 65th minute
        # - Goals scored by Group B team in min 65-80 vs 80-90+
        # - Goals conceded by Group B team in min 65-80 vs 80-90+
        events = self.db.get_events()
        
        match_features = []
        
        for idx, row in matches.iterrows():
            match_id = row["match_id"]
            m_events = events[events["match_id"] == match_id].sort_values("minute")
            
            # Determine which team is Group A vs Group B
            # If both are A or both are B, we still identify but mark asymmetry as 0
            g_home = row["gdp_group_home"]
            g_away = row["gdp_group_away"]
            
            # Goal tracker by minute
            home_goals_min = []
            away_goals_min = []
            
            for _, ev in m_events.iterrows():
                if ev["event_type"] in ["goal", "penalty"]:
                    if ev["team"] == row["team_home"]:
                        home_goals_min.append(ev["minute"])
                    else:
                        away_goals_min.append(ev["minute"])
                elif ev["event_type"] == "own_goal":
                    # Own goal goes to the opponent
                    if ev["team"] == row["team_home"]:
                        away_goals_min.append(ev["minute"])
                    else:
                        home_goals_min.append(ev["minute"])

            # Compute score at minute 65
            home_score_65 = sum(1 for m in home_goals_min if m < 65)
            away_score_65 = sum(1 for m in away_goals_min if m < 65)
            
            # Compute goals post-65
            home_goals_65_80 = sum(1 for m in home_goals_min if 65 <= m < 80)
            away_goals_65_80 = sum(1 for m in away_goals_min if 65 <= m < 80)
            
            home_goals_80_90 = sum(1 for m in home_goals_min if 80 <= m)
            away_goals_80_90 = sum(1 for m in away_goals_min if 80 <= m)

            # Match state features
            score_at_break = f"{home_score_65}-{away_score_65}"
            
            # Is Group B team leading at 65?
            b_leading_65 = False
            b_team = None
            a_team = None
            
            if g_home == "B" and g_away == "A":
                b_team, a_team = row["team_home"], row["team_away"]
                b_leading_65 = home_score_65 > away_score_65
                goals_conceded_65_80 = away_goals_65_80
                goals_scored_65_80 = home_goals_65_80
                goals_conceded_80_90 = away_goals_80_90
                goals_scored_80_90 = home_goals_80_90
                gdp_diff = row["gdp_home"] - row["gdp_away"]
                rank_diff = row["fifa_rank_home"] - row["fifa_rank_away"]
                squad_ratio = row["squad_value_home_m"] / max(row["squad_value_away_m"], 1.0)
            elif g_home == "A" and g_away == "B":
                b_team, a_team = row["team_away"], row["team_home"]
                b_leading_65 = away_score_65 > home_score_65
                goals_conceded_65_80 = home_goals_65_80
                goals_scored_65_80 = away_goals_65_80
                goals_conceded_80_90 = home_goals_80_90
                goals_scored_80_90 = away_goals_80_90
                gdp_diff = row["gdp_away"] - row["gdp_home"]
                rank_diff = row["fifa_rank_away"] - row["fifa_rank_home"]
                squad_ratio = row["squad_value_away_m"] / max(row["squad_value_home_m"], 1.0)
            else:
                # Same GDP group, pick home as proxy B just to keep column shape populated
                b_team, a_team = row["team_home"], row["team_away"]
                b_leading_65 = home_score_65 > away_score_65
                goals_conceded_65_80 = away_goals_65_80
                goals_scored_65_80 = home_goals_65_80
                goals_conceded_80_90 = away_goals_80_90
                goals_scored_80_90 = home_goals_80_90
                gdp_diff = 0.0
                rank_diff = 0
                squad_ratio = 1.0

            # Momentum shift (R2-4 score trajectory shift)
            # goals conceded post-break minus goals conceded pre-break (last 20 mins: 45-65)
            home_goals_45_65 = sum(1 for m in home_goals_min if 45 <= m < 65)
            away_goals_45_65 = sum(1 for m in away_goals_min if 45 <= m < 65)
            
            if g_home == "B" and g_away == "A":
                conceded_45_65 = away_goals_45_65
            elif g_home == "A" and g_away == "B":
                conceded_45_65 = home_goals_45_65
            else:
                conceded_45_65 = away_goals_45_65
                
            trajectory_shift = goals_conceded_65_80 - conceded_45_65

            match_features.append({
                "match_id": match_id,
                "score_at_break": score_at_break,
                "group_b_team": b_team,
                "group_a_team": a_team,
                "group_b_leading_65": int(b_leading_65),
                "goals_conceded_65_80": goals_conceded_65_80,
                "goals_scored_65_80": goals_scored_65_80,
                "goals_conceded_80_90": goals_conceded_80_90,
                "goals_scored_80_90": goals_scored_80_90,
                "goals_conceded_post_break": goals_conceded_65_80 + goals_conceded_80_90,
                "goals_conceded_45_65": conceded_45_65,
                "trajectory_shift": trajectory_shift,
                "gdp_difference": gdp_diff,
                "rank_difference": rank_diff,
                "squad_value_ratio": squad_ratio,
                "had_hydration_break": int(row["break_likely"]),
            })

        df_features = pd.DataFrame(match_features)
        
        # Merge back to matches
        final_df = matches.merge(df_features, on="match_id", how="left")
        
        # Set final output columns
        final_df["_source"] = "feature_engineer"
        
        # Write to Parquet and SQLite
        parquet_path = os.path.join(str(config.PROCESSED_DIR), "analysis_dataset.parquet")
        final_df.to_parquet(parquet_path, index=False)
        print(f"Saved engineered dataset to Parquet at: {parquet_path}")
        
        with sqlite3.connect(config.DB_PATH) as conn:
            final_df.to_sql("analysis_dataset", conn, if_exists="replace", index=False)
        print("Saved analysis_dataset table to SQLite.")
        
        return final_df

if __name__ == "__main__":
    engineer = FeatureEngineer()
    engineer.engineer_features()
