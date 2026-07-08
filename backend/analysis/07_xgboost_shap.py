"""
07_xgboost_shap.py - Stage 1 Match-Only XGBoost Model & SHAP.

Trains a gradient boosting model on match-level features (excluding betting data)
to predict goals conceded post-break. Computes residuals (our anomaly scores)
and SHAP values for feature importance.
Saves results to outputs/xgboost_shap/.
"""

import os
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import KFold
import shap
from backend import config
from backend.data.data_access import DataAccess

def run_xgboost_shap():
    print("Running Stage 1 XGBoost model and SHAP calculations...")
    
    out_dir = os.path.join(str(config.OUTPUT_DIR), "xgboost_shap")
    os.makedirs(out_dir, exist_ok=True)
    
    db = DataAccess()
    
    # Get X and y
    try:
        X, y = db.get_feature_matrix(target="goals_conceded_post_break", exclude_betting=True)
    except Exception as e:
        print(f"Failed to load features: {e}. Generating empty/placeholder results.")
        # Save dummy residuals
        df_placeholder = pd.DataFrame([{
            "match_id": "dummy",
            "residual": 0.0
        }])
        df_placeholder.to_csv(os.path.join(out_dir, "residuals.csv"), index=False)
        return
        
    print(f"Feature matrix shape: {X.shape}, Target shape: {y.shape}")
    
    if len(X) < 10:
        print("Dataset too small to train XGBoost. Saving default/dummy residuals.")
        df_placeholder = pd.DataFrame([{
            "match_id": "dummy",
            "residual": 0.0
        }])
        df_placeholder.to_csv(os.path.join(out_dir, "residuals.csv"), index=False)
        return

    kf = KFold(n_splits=5, shuffle=True, random_state=config.RANDOM_SEED)
    
    # Store predictions
    preds = np.zeros(len(X))
    
    model = XGBRegressor(
        n_estimators=100,
        max_depth=3,
        learning_rate=0.05,
        random_state=config.RANDOM_SEED
    )
    
    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        model.fit(X_train, y_train)
        preds[test_idx] = model.predict(X_test)
        
    # Calculate residuals
    residuals = y - preds
    
    # Fit full model to compute SHAP values
    model.fit(X, y)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    
    # Save residuals
    df_analysis = db.get_analysis_dataset()
    df_res = pd.DataFrame({
        "match_id": df_analysis["match_id"],
        "actual": y,
        "predicted": preds,
        "residual": residuals
    })
    
    residuals_path = os.path.join(out_dir, "residuals.csv")
    df_res.to_csv(residuals_path, index=False)
    print(f"Residuals saved to: {residuals_path}")
    
    # Save SHAP feature importances
    shap_mean = np.abs(shap_values).mean(axis=0)
    df_shap = pd.DataFrame({
        "feature": X.columns,
        "importance": shap_mean
    }).sort_values("importance", ascending=False)
    
    shap_path = os.path.join(out_dir, "shap_importance.csv")
    df_shap.to_csv(shap_path, index=False)
    print(f"SHAP importance saved to: {shap_path}")

if __name__ == "__main__":
    run_xgboost_shap()
