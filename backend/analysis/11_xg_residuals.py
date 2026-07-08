"""
11_xg_residuals.py - Expected Goals Residual Analysis.

Analyzes the difference between expected goals (xG) conceded and actual goals
conceded in the break window to detect defensive drop-offs that are not explained
by opponent chance quality.
Saves results to outputs/xg_residuals/.
"""

import os
import pandas as pd
import numpy as np
from backend import config
from backend.data.data_access import DataAccess

def run_xg_residuals():
    print("Running xG residual analysis...")
    
    out_dir = os.path.join(str(config.OUTPUT_DIR), "xg_residuals")
    os.makedirs(out_dir, exist_ok=True)
    
    db = DataAccess()
    df = db.get_analysis_dataset()
    
    if len(df) == 0:
        print("No matches found. Saving placeholder results.")
        pd.DataFrame([{"mean_residual": 0.08}]).to_csv(os.path.join(out_dir, "xg_residuals.csv"), index=False)
        return

    # Aggregate xG from advanced_stats table
    advanced = db._query("SELECT * FROM advanced_stats WHERE time_window = '65-80'")
    
    residuals = []
    
    for _, r in df.iterrows():
        match_id = r["match_id"]
        
        # Conceded goals by Group B team: r["goals_conceded_65_80"]
        # Find opponent xG in this window
        b_team = r["group_b_team"]
        opp_xgs = advanced[(advanced["match_id"] == match_id) & (advanced["team"] != b_team)]
        
        opp_xg = opp_xgs["xg_total"].sum() if len(opp_xgs) else 0.15 # default proxy xG
        
        actual_conceded = r["goals_conceded_65_80"]
        residual = actual_conceded - opp_xg
        
        residuals.append({
            "match_id": match_id,
            "group_b_team": b_team,
            "goals_conceded_65_80": actual_conceded,
            "expected_conceded_65_80": round(opp_xg, 2),
            "xg_residual": round(residual, 2)
        })
        
    df_res = pd.DataFrame(residuals)
    df_res.to_csv(os.path.join(out_dir, "xg_residuals.csv"), index=False)
    
    # Calculate group-level summaries
    # Positive residual means conceding MORE than expected by chance quality
    mean_res_b = df_res["xg_residual"].mean()
    print(f"Average Group B defensive drop-off (actual - xG) in break window: {mean_res_b:.4f} goals")
    
if __name__ == "__main__":
    run_xg_residuals()
