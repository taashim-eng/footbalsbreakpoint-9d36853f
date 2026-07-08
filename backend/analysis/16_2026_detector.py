"""
16_2026_detector.py - 2026 Anomaly Detector.

Isolates 2026 World Cup fixtures, merges their composite anomaly index,
and outputs a clean, monitor-ready dataset with anomaly levels.
Saves results to outputs/2026_monitor/.
"""

import os
import pandas as pd
from backend import config
from backend.data.data_access import DataAccess

def run_2026_detector():
    print("Running 2026 World Cup anomaly detector monitor...")
    
    out_dir = os.path.join(str(config.OUTPUT_DIR), "2026_monitor")
    os.makedirs(out_dir, exist_ok=True)
    
    db = DataAccess()
    
    # Load 2026 matches
    df_2026 = db.get_matches(era="C")
    
    if len(df_2026) == 0:
        print("No 2026 matches found in matches table. Saving placeholder.")
        pd.DataFrame([{"match_id": "dummy", "anomaly_level": "normal"}]).to_csv(os.path.join(out_dir, "monitor_results.csv"), index=False)
        return

    # Load composite anomaly index
    idx_path = os.path.join(str(config.OUTPUT_DIR), "anomaly_index", "anomaly_index.csv")
    if not os.path.exists(idx_path):
        import importlib
        mod = importlib.import_module("backend.analysis.15_anomaly_index")
        calculate_anomaly_index = getattr(mod, "calculate_anomaly_index")
        calculate_anomaly_index()
        
    df_idx = pd.read_csv(idx_path)
    
    # Merge matches with index
    df_monitor = df_2026.merge(df_idx, on="match_id", how="left")
    
    # Fill in GDP group flags for home/away
    # Add gdp_group columns
    df_analysis = db.get_analysis_dataset(era="C")
    df_monitor = df_monitor.merge(
        df_analysis[["match_id", "gdp_group_home", "gdp_group_away", "group_b_team", "group_b_leading_65", "goals_conceded_65_80"]],
        on="match_id",
        how="left"
    )
    
    # Save the 2026 specific monitor dataset
    monitor_path = os.path.join(out_dir, "monitor_results.csv")
    df_monitor.to_csv(monitor_path, index=False)
    print(f"2026 anomaly monitor dataset saved: {monitor_path}")
    
    # Count of anomalies in 2026
    counts = df_monitor["anomaly_level"].value_counts().to_dict()
    print(f"2026 Anomaly breakdown: {counts}")

if __name__ == "__main__":
    run_2026_detector()
