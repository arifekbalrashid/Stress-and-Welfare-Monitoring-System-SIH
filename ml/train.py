"""
SAATHI ML — Training Script
Trains Logistic Regression + XGBoost classifiers on synthetic welfare risk data.

Usage:
    python train.py                         # defaults
    python train.py --data path/to/data.csv # custom data
    python train.py --artifacts-dir ./out   # custom output dir

Outputs (written to artifacts dir):
    logistic_regression_v1.joblib   — LR pipeline (scaler + model)
    xgboost_v1.joblib               — XGBoost model
    label_encoder_v1.joblib         — LabelEncoder for risk_level
    training_report_v1.json         — full metrics report
    confusion_matrix_lr.png         — LR confusion matrix
    confusion_matrix_xgb.png        — XGBoost confusion matrix
    shap_summary.png                — SHAP feature importance bar plot
    feature_importance_xgb.png      — XGBoost native feature importance
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import xgboost as xgb

# Local imports
from evaluate import (
    RISK_LEVELS,
    compute_metrics,
    save_classification_report,
    plot_confusion_matrix,
    plot_shap_summary,
    plot_feature_importance,
)

# ── Constants ───────────────────────────────────────────────────────

DEFAULT_DATA = os.path.join(os.path.dirname(__file__), "synthetic_saathi_training_v1.csv")
DEFAULT_FEATURES_CFG = os.path.join(os.path.dirname(__file__), "config", "model_features_v1.json")
DEFAULT_ARTIFACTS = os.path.join(os.path.dirname(__file__), "artifacts")

RANDOM_STATE = 42
TEST_SIZE = 0.20

TARGET_COL = "risk_level"
SCORE_COL = "risk_score"


# ── Helpers ─────────────────────────────────────────────────────────

def load_feature_config(path: str) -> list[str]:
    """Load the feature list from the JSON config."""
    with open(path) as f:
        cfg = json.load(f)
    return cfg["features"]


def load_data(csv_path: str, feature_cols: list[str]):
    """Load CSV and return feature DataFrame + target Series.

    Missing values in temporal/derived columns are expected for early-week
    rows (e.g., previous_risk_score, *_change_pct). We keep them as NaN
    for XGBoost (handles natively) and impute for LR later.
    """
    df = pd.read_csv(csv_path)

    # Validate columns exist
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns in data: {missing}")
    if TARGET_COL not in df.columns:
        raise ValueError(f"Target column '{TARGET_COL}' not found in data.")

    # Normalise risk_level labels to title case
    df[TARGET_COL] = df[TARGET_COL].str.strip().str.title()

    X = df[feature_cols].copy()
    y = df[TARGET_COL].copy()

    print(f"✓ Loaded {len(df):,} rows, {len(feature_cols)} features")
    print(f"  Class distribution:\n{y.value_counts().to_string()}\n")

    return X, y, df


def build_logistic_regression(X_train, y_train_encoded, feature_cols):
    """Train a Logistic Regression pipeline (StandardScaler → LR).

    LR cannot handle NaN, so we impute with median before scaling.
    """
    X_filled = X_train.copy()
    medians = X_filled.median()
    X_filled = X_filled.fillna(medians)

    scaler = StandardScaler()
    lr = LogisticRegression(
        max_iter=1000,
        multi_class="multinomial",
        solver="lbfgs",
        random_state=RANDOM_STATE,
        class_weight="balanced",
    )

    pipeline = Pipeline([("scaler", scaler), ("lr", lr)])
    pipeline.fit(X_filled, y_train_encoded)

    return pipeline, medians


def build_xgboost(X_train, y_train_encoded, num_classes):
    """Train an XGBoost classifier. XGBoost handles NaN natively."""
    model = xgb.XGBClassifier(
        objective="multi:softprob",
        num_class=num_classes,
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=RANDOM_STATE,
        eval_metric="mlogloss",
        use_label_encoder=False,
        enable_categorical=False,
        tree_method="hist",   # fast, handles NaN
    )
    model.fit(X_train, y_train_encoded, verbose=False)
    return model


# ── Main ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SAATHI ML Training")
    parser.add_argument("--data", default=DEFAULT_DATA, help="Path to training CSV")
    parser.add_argument("--features-config", default=DEFAULT_FEATURES_CFG, help="Feature config JSON")
    parser.add_argument("--artifacts-dir", default=DEFAULT_ARTIFACTS, help="Output artifacts directory")
    args = parser.parse_args()

    artifacts_dir = Path(args.artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  SAATHI — ML Model Training")
    print("=" * 60)
    start_time = time.time()

    # ── 1. Load data ────────────────────────────────────────────
    feature_cols = load_feature_config(args.features_config)
    X, y, df = load_data(args.data, feature_cols)

    # Encode target
    le = LabelEncoder()
    le.classes_ = np.array(RISK_LEVELS)  # enforce consistent ordering
    y_encoded = le.transform(y)

    # ── 2. Split ────────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y_encoded
    )
    print(f"✓ Split: {len(X_train):,} train / {len(X_test):,} test")

    # ── 3. Train Logistic Regression ────────────────────────────
    print("\n── Logistic Regression ──")
    lr_pipeline, lr_medians = build_logistic_regression(X_train, y_train, feature_cols)

    # Predict (need to fill NaN for LR)
    X_test_filled = X_test.fillna(lr_medians)
    lr_pred = lr_pipeline.predict(X_test_filled)
    lr_proba = lr_pipeline.predict_proba(X_test_filled)

    lr_pred_labels = le.inverse_transform(lr_pred)
    y_test_labels = le.inverse_transform(y_test)

    lr_metrics = compute_metrics(y_test_labels, lr_pred_labels, lr_proba, labels=RISK_LEVELS)
    print(f"  Accuracy: {lr_metrics['accuracy']:.4f}")
    print(f"  Macro F1: {lr_metrics['macro_f1']:.4f}")
    if lr_metrics.get("auc_roc"):
        print(f"  AUC-ROC:  {lr_metrics['auc_roc']:.4f}")

    # Coefficient analysis
    lr_model = lr_pipeline.named_steps["lr"]
    coef_importance = np.abs(lr_model.coef_).mean(axis=0)
    lr_feature_importance = {
        feat: round(float(imp), 4)
        for feat, imp in zip(feature_cols, coef_importance)
    }

    # ── 4. Train XGBoost ────────────────────────────────────────
    print("\n── XGBoost ──")
    xgb_model = build_xgboost(X_train, y_train, num_classes=len(RISK_LEVELS))

    xgb_pred = xgb_model.predict(X_test)
    xgb_proba = xgb_model.predict_proba(X_test)

    xgb_pred_labels = le.inverse_transform(xgb_pred)

    xgb_metrics = compute_metrics(y_test_labels, xgb_pred_labels, xgb_proba, labels=RISK_LEVELS)
    print(f"  Accuracy: {xgb_metrics['accuracy']:.4f}")
    print(f"  Macro F1: {xgb_metrics['macro_f1']:.4f}")
    if xgb_metrics.get("auc_roc"):
        print(f"  AUC-ROC:  {xgb_metrics['auc_roc']:.4f}")

    # XGBoost native feature importance
    xgb_importance = xgb_model.feature_importances_
    xgb_feature_importance = {
        feat: round(float(imp), 4)
        for feat, imp in zip(feature_cols, xgb_importance)
    }

    # ── 5. SHAP (XGBoost) ──────────────────────────────────────
    print("\n── SHAP Explainability ──")
    shap_factors_summary = {}
    try:
        import shap
        explainer = shap.TreeExplainer(xgb_model)
        shap_values = explainer.shap_values(X_test)

        # shap_values is a list of arrays (one per class) for multi-class
        if isinstance(shap_values, list):
            mean_abs = np.abs(np.array(shap_values)).mean(axis=(0, 1))
        elif shap_values.ndim == 3:
            mean_abs = np.abs(shap_values).mean(axis=(0, 2))
        else:
            mean_abs = np.abs(shap_values).mean(axis=0)

        for feat, val in zip(feature_cols, mean_abs):
            shap_factors_summary[feat] = round(float(val), 4)

        # Sort descending
        shap_factors_summary = dict(
            sorted(shap_factors_summary.items(), key=lambda x: x[1], reverse=True)
        )

        # Plot
        plot_shap_summary(
            shap_values, X_test, str(artifacts_dir / "shap_summary.png"),
            feature_names=feature_cols,
        )
        print("  ✓ SHAP summary plot saved")
        print(f"  Top 5 factors: {list(shap_factors_summary.items())[:5]}")

    except Exception as e:
        print(f"  ⚠ SHAP analysis failed: {e}")

    # ── 6. Save artifacts ───────────────────────────────────────
    print("\n── Saving Artifacts ──")

    # Models
    joblib.dump(lr_pipeline, str(artifacts_dir / "logistic_regression_v1.joblib"))
    joblib.dump(xgb_model, str(artifacts_dir / "xgboost_v1.joblib"))
    joblib.dump(le, str(artifacts_dir / "label_encoder_v1.joblib"))
    joblib.dump(lr_medians.to_dict(), str(artifacts_dir / "lr_medians_v1.joblib"))
    print("  ✓ Models saved")

    # Plots
    plot_confusion_matrix(
        y_test_labels, lr_pred_labels,
        str(artifacts_dir / "confusion_matrix_lr.png"),
        title="Logistic Regression — Confusion Matrix",
    )
    plot_confusion_matrix(
        y_test_labels, xgb_pred_labels,
        str(artifacts_dir / "confusion_matrix_xgb.png"),
        title="XGBoost — Confusion Matrix",
    )
    plot_feature_importance(
        xgb_importance, feature_cols,
        str(artifacts_dir / "feature_importance_xgb.png"),
        title="XGBoost — Feature Importance",
    )
    print("  ✓ Plots saved")

    # Classification reports
    save_classification_report(
        y_test_labels, lr_pred_labels,
        str(artifacts_dir / "classification_report_lr.txt"),
    )
    save_classification_report(
        y_test_labels, xgb_pred_labels,
        str(artifacts_dir / "classification_report_xgb.txt"),
    )
    print("  ✓ Classification reports saved")

    # Training report JSON
    elapsed = round(time.time() - start_time, 2)
    report = {
        "model_version": "v1.0",
        "feature_set_version": "v1",
        "features": feature_cols,
        "dataset": {
            "total_rows": len(df),
            "train_rows": len(X_train),
            "test_rows": len(X_test),
            "class_distribution": y.value_counts().to_dict(),
        },
        "logistic_regression": {
            "metrics": lr_metrics,
            "feature_importance": lr_feature_importance,
        },
        "xgboost": {
            "metrics": xgb_metrics,
            "feature_importance": xgb_feature_importance,
            "shap_summary": shap_factors_summary,
            "hyperparameters": {
                "n_estimators": 200,
                "max_depth": 6,
                "learning_rate": 0.1,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
            },
        },
        "training_time_seconds": elapsed,
    }

    with open(str(artifacts_dir / "training_report_v1.json"), "w") as f:
        json.dump(report, f, indent=2)
    print("  ✓ Training report saved")

    # ── 7. Summary ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Training Complete!")
    print(f"  Time: {elapsed}s")
    print(f"  Artifacts: {artifacts_dir.resolve()}")
    print()
    print(f"  {'Model':<25} {'Accuracy':>10} {'Macro F1':>10} {'AUC-ROC':>10}")
    print(f"  {'-'*55}")
    lr_auc = lr_metrics.get('auc_roc')
    xgb_auc = xgb_metrics.get('auc_roc')
    print(f"  {'Logistic Regression':<25} {lr_metrics['accuracy']:>10.4f} {lr_metrics['macro_f1']:>10.4f} {(f'{lr_auc:.4f}' if lr_auc is not None else 'N/A'):>10}")
    print(f"  {'XGBoost':<25} {xgb_metrics['accuracy']:>10.4f} {xgb_metrics['macro_f1']:>10.4f} {(f'{xgb_auc:.4f}' if xgb_auc is not None else 'N/A'):>10}")
    print("=" * 60)

    return report


if __name__ == "__main__":
    main()
