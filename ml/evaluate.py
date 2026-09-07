"""
SAATHI ML — Evaluation Utilities
Classification metrics, confusion matrix, AUC-ROC, and SHAP visualisation.
"""

import json
import numpy as np
import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
    precision_recall_fscore_support,
)


# ── Ordered risk levels (used everywhere) ──────────────────────────
RISK_LEVELS = ["Low", "Moderate", "Elevated", "High"]


def compute_metrics(y_true, y_pred, y_proba=None, labels=None):
    """Return a dict of evaluation metrics.

    Parameters
    ----------
    y_true : array-like  — true labels (string or int-encoded)
    y_pred : array-like  — predicted labels
    y_proba : array-like, optional — predicted probabilities (n_samples × n_classes)
    labels : list, optional — ordered class labels

    Returns
    -------
    dict with accuracy, per-class precision/recall/f1, macro averages, and optional AUC-ROC.
    """
    if labels is None:
        labels = RISK_LEVELS

    acc = accuracy_score(y_true, y_pred)
    prec, rec, f1, sup = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    per_class = {}
    for i, lbl in enumerate(labels):
        per_class[lbl] = {
            "precision": round(float(prec[i]), 4),
            "recall": round(float(rec[i]), 4),
            "f1": round(float(f1[i]), 4),
            "support": int(sup[i]),
        }

    metrics = {
        "accuracy": round(float(acc), 4),
        "macro_precision": round(float(prec.mean()), 4),
        "macro_recall": round(float(rec.mean()), 4),
        "macro_f1": round(float(f1.mean()), 4),
        "per_class": per_class,
        "confusion_matrix": cm.tolist(),
    }

    # AUC-ROC (one-vs-rest)
    if y_proba is not None:
        try:
            auc = roc_auc_score(
                y_true, y_proba, multi_class="ovr", labels=labels, average="macro"
            )
            metrics["auc_roc"] = round(float(auc), 4)
        except ValueError:
            metrics["auc_roc"] = None

    return metrics


def save_classification_report(y_true, y_pred, path, labels=None):
    """Save sklearn classification_report as a text file."""
    if labels is None:
        labels = RISK_LEVELS
    report = classification_report(y_true, y_pred, labels=labels, zero_division=0)
    with open(path, "w") as f:
        f.write(report)
    return report


def plot_confusion_matrix(y_true, y_pred, path, labels=None, title="Confusion Matrix"):
    """Save a confusion matrix heatmap to *path*."""
    if labels is None:
        labels = RISK_LEVELS
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    ax.set_title(title, fontsize=13)
    fig.colorbar(im, ax=ax)

    tick_marks = np.arange(len(labels))
    ax.set_xticks(tick_marks)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=10)
    ax.set_yticks(tick_marks)
    ax.set_yticklabels(labels, fontsize=10)

    # Annotate cells
    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                j, i, format(cm[i, j], "d"),
                ha="center", va="center",
                color="white" if cm[i, j] > thresh else "black",
            )

    ax.set_ylabel("True label")
    ax.set_xlabel("Predicted label")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_shap_summary(shap_values, X, path, feature_names=None, max_display=13):
    """Save a SHAP bar summary plot.

    Parameters
    ----------
    shap_values : shap.Explanation or np.ndarray
    X : DataFrame or array
    path : str — output image path
    feature_names : list, optional
    max_display : int
    """
    try:
        import shap

        fig, ax = plt.subplots(figsize=(8, 6))

        # shap_values can be an Explanation or ndarray
        # For multi-class, shap_values may be a list of arrays
        if isinstance(shap_values, list):
            # Stack all classes and take mean absolute
            stacked = np.abs(np.array(shap_values)).mean(axis=0)  # (n_samples, n_features)
            mean_abs = stacked.mean(axis=0)
        elif hasattr(shap_values, "values"):
            vals = shap_values.values
            if vals.ndim == 3:
                # (n_samples, n_features, n_classes)
                mean_abs = np.abs(vals).mean(axis=(0, 2))
            else:
                mean_abs = np.abs(vals).mean(axis=0)
        else:
            if shap_values.ndim == 3:
                mean_abs = np.abs(shap_values).mean(axis=(0, 2))
            else:
                mean_abs = np.abs(shap_values).mean(axis=0)

        if feature_names is None:
            feature_names = [f"Feature {i}" for i in range(len(mean_abs))]

        sorted_idx = np.argsort(mean_abs)
        ax.barh(
            [feature_names[i] for i in sorted_idx],
            mean_abs[sorted_idx],
            color="#1f77b4",
        )
        ax.set_xlabel("Mean |SHAP value|")
        ax.set_title("Feature Importance (SHAP)")
        fig.tight_layout()
        fig.savefig(path, dpi=150)
        plt.close(fig)

    except Exception as e:
        print(f"⚠  Could not generate SHAP plot: {e}")


def plot_feature_importance(importances, feature_names, path, title="Feature Importance"):
    """Save a horizontal bar chart of feature importances."""
    sorted_idx = np.argsort(importances)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(
        [feature_names[i] for i in sorted_idx],
        importances[sorted_idx],
        color="#2ca02c",
    )
    ax.set_xlabel("Importance")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
