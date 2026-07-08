"""
09_isolation_forest.py - Unsupervised Anomaly Detection.

Applies an Isolation Forest model to multi-dimensional match statistics
(goals, shots, cards, substitutions, rankings) to identify anomalous matches.
Saves results to outputs/isolation_forest/.
"""

import os
import pandas as pd
from sklearn.ensemble import IsolationForest
from backend import config
from backend.data.data_access import DataAccess

def run_isolation_forest():
    print("Running Isolation Forest anomaly detection...")
    
    out_dir = os.path.join(str(config.OUTPUT_DIR), "isolation_forest")
    os.makedirs(out_dir, exist_ok=True)
    
    db = DataAccess()
    
    try:
        X, _ = db.get_feature_matrix(exclude_betting=True)
    except Exception as e:
        print(f"Failed to load features: {e}. Generating placeholder results.")
        pd.DataFrame([{"match_id": "dummy", "anomaly_score": 0.0}]).to_csv(os.path.join(out_dir, "anomaly_scores.csv"), index=False)
        return
        
    if len(X) < 10:
        print("Dataset too small for Isolation Forest. Saving placeholder.")
        pd.DataFrame([{"match_id": "dummy", "anomaly_score": 0.0}]).to_csv(os.path.join(out_dir, "anomaly_scores.csv"), index=False)
        return
        
    print(f"Running Isolation Forest on feature matrix of shape: {X.shape}")
    
    # Train Isolation Forest
    clf = IsolationForest(
        n_estimators=100,
        contamination=0.05,
        random_state=config.RANDOM_SEED
    )
    
    # Fit and get decision scores (lower means more anomalous)
    clf.fit(X)
    scores = clf.decision_function(X)
    
    # Transform score so higher means more anomalous [0, 1] range proxy
    # decision_function outputs range [-0.5, 0.5] approx
    anomaly_index = -scores
    # Scale to [0, 1] approx
    anomaly_index = (anomaly_index - anomaly_index.min()) / max((anomaly_index.max() - anomaly_index.min()), 0.001)
    
    df_analysis = db.get_analysis_dataset()
    df_results = pd.DataFrame({
        "match_id": df_analysis["match_id"],
        "anomaly_score": scores,
        "anomaly_index_scaled": anomaly_index
    })
    
    scores_path = os.path.join(out_dir, "anomaly_scores.csv")
    df_results.to_csv(scores_path, index=False)
    print(f"Isolation Forest anomaly scores saved to: {scores_path}")

if __name__ == "__main__":
    run_isolation_forest()
