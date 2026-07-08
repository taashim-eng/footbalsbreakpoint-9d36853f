"""
01_exploratory.py - Exploratory Data Analysis.

Generates distributions, heatmaps, and summary tables of match goals
and score trajectories, stratified by era and GDP group.
Saves plots and tables to outputs/eda/.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from backend import config
from backend.data.data_access import DataAccess

def run_eda():
    print("Running exploratory data analysis...")
    
    # Target directories
    out_dir = os.path.join(str(config.OUTPUT_DIR), "eda")
    os.makedirs(out_dir, exist_ok=True)
    
    db = DataAccess()
    df = db.get_analysis_dataset()
    
    # Summary of dataset size
    summary_stats = {
        "total_matches": len(df),
        "matches_by_era": df["era"].value_counts().to_dict(),
        "matches_by_group_b_leading": df["group_b_leading_65"].sum(),
    }
    
    print(f"Summary: {summary_stats}")
    
    # Save a summary JSON/CSV
    pd.DataFrame([summary_stats]).to_json(os.path.join(out_dir, "summary.json"), indent=2)
    
    # ── 1. Goal Distribution by Minute (All Eras) ─────────────────────────────────
    events = db.get_events()
    goals = events[events["event_type"].isin(["goal", "penalty", "own_goal"])].copy()
    
    plt.figure(figsize=(10, 5))
    sns.histplot(data=goals, x="minute", bins=18, kde=True, color="#3b82f6")
    plt.axvspan(config.BREAK_WINDOW_START, config.BREAK_WINDOW_END, 
                color="orange", alpha=0.3, label="Break Window (65-80)")
    plt.title("Goal Distribution by Match Minute")
    plt.xlabel("Minute")
    plt.ylabel("Goal Count")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "goal_distribution.png"), dpi=300)
    plt.close()
    
    # ── 2. Era B & C Break Window Comparison ──────────────────────────────────────
    # We want to see if the goals conceded rate differs in 65-80 window
    # between Group A and Group B teams.
    df_window = df[df["era"].isin(["B", "C"])].copy()
    
    plt.figure(figsize=(8, 5))
    sns.boxplot(data=df_window, x="gdp_group_home", y="goals_conceded_65_80", hue="era", palette="Set2")
    plt.title("Goals Conceded in Break Window (65-80) by GDP Group")
    plt.xlabel("GDP Group")
    plt.ylabel("Goals Conceded")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "goals_conceded_65_80.png"), dpi=300)
    plt.close()
    
    # ── 3. Score Trajectory Momentum Shift ────────────────────────────────────────
    # Track average score difference shift before vs after break
    # trajectory_shift = goals_conceded_65_80 - goals_conceded_45_65
    plt.figure(figsize=(8, 5))
    sns.violinplot(data=df, x="era", y="trajectory_shift", hue="gdp_group_home", split=True, inner="quart", palette="muted")
    plt.axhline(0, color="gray", linestyle="--")
    plt.title("Score Trajectory Shift (Post vs Pre Break Window)")
    plt.xlabel("Era")
    plt.ylabel("Conceded Shift (65-80 vs 45-65)")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "trajectory_shift.png"), dpi=300)
    plt.close()

    print("EDA completed successfully.")

if __name__ == "__main__":
    run_eda()
