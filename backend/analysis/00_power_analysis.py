"""
00_power_analysis.py - Statistical power simulation.

Estimates the statistical power and minimum detectable effect sizes (MDE)
given our sample size constraints. Saves results to outputs/power_analysis/.
"""

import os
import numpy as np
import pandas as pd
import scipy.stats as stats
from backend import config

def run_power_analysis():
    print("Running power analysis simulation...")
    
    # Target outputs directory
    out_dir = os.path.join(str(config.OUTPUT_DIR), "power_analysis")
    os.makedirs(out_dir, exist_ok=True)
    
    # Configuration
    # Total matches in Era C (2026): 104 matches
    # Effective sample of matches where Group B is leading or drawing at min 65: ~40 matches
    # Let's run simulation for two-sample comparison: Group B vs Group A
    # under different sample sizes (N) and effect sizes (d)
    
    np.random.seed(config.RANDOM_SEED)
    
    sample_sizes = [20, 40, 60, 80, 100, 150, 200, 300]
    effect_sizes = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8]
    alpha = 0.05 / config.N_PRIMARY_HYPOTHESES # Bonferroni / BH family-wise alpha threshold
    
    results = []
    
    for n in sample_sizes:
        for d in effect_sizes:
            # Simulate 1000 experiments
            rejections = 0
            for _ in range(1000):
                # Group A baseline goal rate: mean 0.15 goals in break window
                # Group B: mean 0.15 + d * standard_deviation
                # Goal distributions are Poisson or negative binomial, we model Poisson here
                mu_a = 0.15
                std_a = np.sqrt(mu_a) # Poisson std is sqrt(mu)
                mu_b = mu_a + d * std_a
                
                group_a = np.random.poisson(mu_a, n)
                group_b = np.random.poisson(mu_b, n)
                
                # Run t-test or Mann-Whitney U test
                stat, p_val = stats.ttest_ind(group_a, group_b)
                if p_val < alpha:
                    rejections += 1
            
            power = rejections / 1000.0
            results.append({
                "sample_size": n,
                "effect_size": d,
                "power": power
            })
            
    df_power = pd.DataFrame(results)
    
    # Save raw CSV
    csv_path = os.path.join(out_dir, "power_curves.csv")
    df_power.to_csv(csv_path, index=False)
    print(f"Power analysis curves saved to: {csv_path}")
    
    # Compute MDE at 80% power
    mde_records = []
    for n in sample_sizes:
        df_n = df_power[df_power["sample_size"] == n]
        # Interpolate effect size that gives 80% power
        # If all below 80%, pick max
        above_80 = df_n[df_n["power"] >= 0.80]
        if len(above_80):
            mde = above_80["effect_size"].min()
        else:
            mde = df_n["effect_size"].max()
            
        mde_records.append({
            "sample_size": n,
            "detectable_effect": round(mde, 2)
        })
        
    df_mde = pd.DataFrame(mde_records)
    mde_csv_path = os.path.join(out_dir, "mde_summary.csv")
    df_mde.to_csv(mde_csv_path, index=False)
    print(f"MDE summary saved to: {mde_csv_path}")

if __name__ == "__main__":
    run_power_analysis()
