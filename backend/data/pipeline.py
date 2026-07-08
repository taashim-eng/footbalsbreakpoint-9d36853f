"""
Master Data Pipeline - DAG-ordered data collection and integration.

Runs all 7 collectors in dependency order, normalises team names and match IDs,
validates the integrated data, and writes the results to SQLite and Parquet.
"""

import os
import sqlite3
import pandas as pd
from backend import config
from backend.data.collectors.match_collector import MatchCollector
from backend.data.collectors.event_collector import EventCollector
from backend.data.collectors.gdp_collector import GDPCollector
from backend.data.collectors.weather_collector import WeatherCollector
from backend.data.collectors.rankings_collector import RankingsCollector
from backend.data.collectors.betting_collector import BettingCollector
from backend.data.collectors.advanced_stats_collector import AdvancedStatsCollector
from backend.data.match_id_resolver import MatchIDResolver
from backend.data.validation import DataValidator

def run_pipeline(force: bool = False):
    print("=== STARTING THE BREAK POINT DATA PIPELINE ===")
    
    # Ensure processed directory exists
    os.makedirs(config.PROCESSED_DIR, exist_ok=True)
    
    # ── Step 1: Independent Collectors (Parallel in theory, sequential here) ────────
    print("\n[Step 1] Running independent collectors...")
    gdp_df = GDPCollector().collect(force=force)
    match_df = MatchCollector().collect(force=force)
    
    # ── Step 2: Dependent Collectors ───────────────────────────────────────────────
    print("\n[Step 2] Running dependent collectors...")
    event_df = EventCollector().collect(force=force)
    weather_df = WeatherCollector(match_df).collect(force=force)
    betting_df = BettingCollector().collect(force=force)
    rankings_df = RankingsCollector(match_df).collect(force=force)
    
    # ── Step 3: Second-Order Dependencies ──────────────────────────────────────────
    print("\n[Step 3] Running advanced stats collector...")
    advanced_df = AdvancedStatsCollector(event_df).collect(force=force)

    # ── Step 4: Normalisation & Match ID Resolution ────────────────────────────────
    print("\n[Step 4] Resolving names and match IDs...")
    resolver = MatchIDResolver()
    
    # Standardise match IDs for all tables using resolver
    # Match collector already generates resolved ids, but let's make sure
    match_df = resolver.unify_dataframe(match_df, ["team_home", "team_away"])
    
    # Events mapping
    # Fjelstul event collector tries its best, but let's map team names and re-hash IDs
    # using our canonical mapping table for completeness
    event_df["team"] = event_df["team"].apply(resolver.canonical)
    
    # For betting, ensure team home/away mapping or match_id unification
    # Rankings team normalization
    rankings_df["team"] = rankings_df["team"].apply(resolver.canonical)
    
    # ── Step 5: Data Validation ────────────────────────────────────────────────────
    print("\n[Step 5] Running validation layer...")
    validator = DataValidator()
    
    val_matches = validator.validate_matches(match_df)
    match_ids = set(match_df["match_id"])
    
    val_events = validator.validate_events(event_df, match_ids)
    val_gdp = validator.validate_gdp(gdp_df)
    val_weather = validator.validate_weather(weather_df, match_ids)
    
    validator.validate_foreign_keys(event_df, weather_df, betting_df, match_ids)
    
    # Log coverage
    cov_df = validator.coverage_by_tournament(match_df, event_df)
    print("\nEvent coverage by tournament:")
    print(cov_df.to_string(index=False))
    
    # Generate report
    report_path = os.path.join(str(config.OUTPUT_DIR), "data_quality_report.md")
    validator.generate_report(report_path)
    print(f"Data quality report written to: {report_path}")
    
    # ── Step 6: Persist to SQLite Database ──────────────────────────────────────────
    print(f"\n[Step 6] Saving tables to SQLite database at: {config.DB_PATH}")
    with sqlite3.connect(config.DB_PATH) as conn:
        match_df.to_sql("matches", conn, if_exists="replace", index=False)
        event_df.to_sql("events", conn, if_exists="replace", index=False)
        gdp_df.to_sql("gdp", conn, if_exists="replace", index=False)
        weather_df.to_sql("weather", conn, if_exists="replace", index=False)
        rankings_df.to_sql("rankings", conn, if_exists="replace", index=False)
        betting_df.to_sql("betting", conn, if_exists="replace", index=False)
        advanced_df.to_sql("advanced_stats", conn, if_exists="replace", index=False)
        
    print("Pipeline run completed successfully.")

if __name__ == "__main__":
    import sys
    force_run = "--force" in sys.argv
    run_pipeline(force=force_run)
