"""
Master Analysis Runner - Executes all 17 analysis modules in sequence.
Uses importlib to dynamically load modules starting with numbers.
"""

import importlib

def run_all():
    print("=== STARTING THE BREAK POINT STATISTICAL ANALYSIS PROCESS ===")
    
    modules = [
        ("backend.analysis.00_power_analysis", "run_power_analysis"),
        ("backend.analysis.01_exploratory", "run_eda"),
        ("backend.analysis.02_era_a_baseline", "run_era_a_baseline"),
        ("backend.analysis.03_era_b_quasi_experiment", "run_era_b_analysis"),
        ("backend.analysis.04_era_c_natural_experiment", "run_era_c_analysis"),
        ("backend.analysis.05_survival", "run_survival_analysis"),
        ("backend.analysis.06_win_probability", "run_win_prob_analysis"),
        ("backend.analysis.07_xgboost_shap", "run_xgboost_shap"),
        ("backend.analysis.08_chi_squared", "run_chi_squared"),
        ("backend.analysis.09_isolation_forest", "run_isolation_forest"),
        ("backend.analysis.10_propensity_matching", "run_propensity_matching"),
        ("backend.analysis.11_xg_residuals", "run_xg_residuals"),
        ("backend.analysis.12_betting_stage2_odds", "run_betting_odds_analysis"),
        ("backend.analysis.13_betting_stage2_volume", "run_volume_analysis"),
        ("backend.analysis.14_betting_stage2_efficiency", "run_efficiency_analysis"),
        ("backend.analysis.15_anomaly_index", "calculate_anomaly_index"),
        ("backend.analysis.16_2026_detector", "run_2026_detector"),
        ("backend.analysis.17_anomaly_enrichment", "run_anomaly_enrichment")
    ]
    
    for mod_path, func_name in modules:
        print(f"\nRunning {mod_path} -> {func_name}...")
        try:
            mod = importlib.import_module(mod_path)
            func = getattr(mod, func_name)
            func()
        except Exception as e:
            print(f"Error running {mod_path}: {e}")
            raise e
            
    print("\n=== ALL ANALYSIS MODULES EXECUTED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_all()
