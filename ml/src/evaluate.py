"""
evaluate.py - Model evaluation on held-out test partition.

This script:
1. Loads the serialized model (model.pkl) and scaler (scaler.pkl).
2. Generates test predictions on the held-out 20% test split.
3. Computes comprehensive classification metrics:
   - Overall Accuracy
   - Macro & Weighted Precision, Recall, and F1-Score
   - Per-class breakdown (precision, recall, f1-score, support)
4. Saves high-resolution evaluation figures:
   - ml/models/confusion_matrix.png
   - ml/models/feature_importance.png
5. Exports structured JSON metrics to ml/models/metrics.json for reports/dashboards.
6. Prints a clean, presentation-ready per-class performance report.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless figure generation
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

# Allow imports when running as standalone script or as a module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from ml.src.features import FEATURE_ORDER, FAULT_LABELS
from ml.src.preprocessing import (
    load_data,
    clean_data,
    split_and_scale_data,
    load_scaler,
    DEFAULT_MODELS_DIR,
    DEFAULT_DATA_DIR
)
from ml.src.train import MODEL_FILENAME

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CONFUSION_MATRIX_FILENAME = "confusion_matrix.png"
FEATURE_IMPORTANCE_FILENAME = "feature_importance.png"
METRICS_FILENAME = "metrics.json"


def plot_and_save_confusion_matrix(
    cm: np.ndarray,
    class_names: list,
    output_path: Path
) -> None:
    """
    Plots and saves an aesthetic, high-resolution annotated confusion matrix heatmap.

    Args:
        cm: 2D confusion matrix array.
        class_names: List of class label strings.
        output_path: Destination PNG path.
    """
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    
    # Calculate percentage annotations
    cm_norm = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis]
    annot = np.empty_like(cm).astype(str)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            annot[i, j] = f"{cm[i, j]:,}\n({cm_norm[i, j]:.1%})"

    sns.heatmap(
        cm,
        annot=annot,
        fmt="",
        cmap="Blues",
        cbar=True,
        xticklabels=class_names,
        yticklabels=class_names,
        linewidths=1.2,
        linecolor="#e2e8f0",
        ax=ax
    )

    ax.set_title("Engine Fault Classification - Test Set Confusion Matrix", fontsize=13, fontweight="bold", pad=14)
    ax.set_xlabel("Predicted Fault Class", fontsize=11, fontweight="bold", labelpad=10)
    ax.set_ylabel("True Fault Class", fontsize=11, fontweight="bold", labelpad=10)
    plt.xticks(rotation=15, ha="right", fontsize=10)
    plt.yticks(rotation=0, fontsize=10)
    plt.tight_layout()

    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Confusion matrix plot saved to {output_path}")


def plot_and_save_feature_importance(
    importances: np.ndarray,
    feature_names: list,
    output_path: Path
) -> None:
    """
    Plots and saves horizontal bar chart ranking sensor feature importances.

    Args:
        importances: 1D array of feature importance scores.
        feature_names: List of corresponding feature names.
        output_path: Destination PNG path.
    """
    indices = np.argsort(importances)
    sorted_features = [feature_names[i] for i in indices]
    sorted_importances = importances[indices]

    fig, ax = plt.subplots(figsize=(9, 6), dpi=300)
    bars = ax.barh(range(len(sorted_features)), sorted_importances * 100, color="#2563eb", edgecolor="#1d4ed8", height=0.65)

    ax.set_yticks(range(len(sorted_features)))
    ax.set_yticklabels(sorted_features, fontsize=10)
    ax.set_xlabel("Gini Importance (%)", fontsize=11, fontweight="bold", labelpad=8)
    ax.set_title("Random Forest Sensor Feature Importance Breakdown", fontsize=13, fontweight="bold", pad=14)
    ax.grid(axis="x", linestyle="--", alpha=0.6)

    # Add numeric value label next to each bar
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.3, bar.get_y() + bar.get_height()/2, f"{width:.2f}%",
                va="center", ha="left", fontsize=9, color="#1e293b", fontweight="500")

    ax.set_xlim(0, max(sorted_importances * 100) * 1.15)
    plt.tight_layout()

    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Feature importance plot saved to {output_path}")


def evaluate_model(
    models_dir: Path = DEFAULT_MODELS_DIR,
    data_dir: Path = DEFAULT_DATA_DIR
) -> Dict[str, Any]:
    """
    Performs full evaluation of the trained model against the test dataset.

    Args:
        models_dir: Path to directory containing model.pkl and scaler.pkl.
        data_dir: Path to data directory.

    Returns:
        Dictionary containing all evaluation metrics.
    """
    models_dir = Path(models_dir)
    model_path = models_dir / MODEL_FILENAME
    scaler_path = models_dir / "scaler.pkl"

    if not model_path.exists():
        raise FileNotFoundError(f"Model artifact not found at {model_path}. Run train.py first.")

    # 1. Load dataset & prepare stratified test partition
    df_raw = load_data()
    df_clean = clean_data(df_raw)
    X_train_scaled, X_test_scaled, y_train, y_test, scaler = split_and_scale_data(
        df_clean,
        test_size=0.2,
        random_state=42
    )

    # 2. Load trained model
    logger.info(f"Loading trained model from {model_path}...")
    model = joblib.load(str(model_path))

    # 3. Generate predictions
    logger.info("Computing predictions on held-out test split...")
    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)

    # 4. Compute overall metrics
    acc = float(accuracy_score(y_test, y_pred))
    prec_macro = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
    prec_weighted = float(precision_score(y_test, y_pred, average="weighted", zero_division=0))
    rec_macro = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
    rec_weighted = float(recall_score(y_test, y_pred, average="weighted", zero_division=0))
    f1_macro = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
    f1_weighted = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))

    cm = confusion_matrix(y_test, y_pred)
    class_names = [FAULT_LABELS[i] for i in range(len(FAULT_LABELS))]
    report_dict = classification_report(y_test, y_pred, target_names=class_names, output_dict=True, zero_division=0)

    # 5. Extract Feature Importances
    importances = model.feature_importances_
    feat_importance_dict = {
        FEATURE_ORDER[i]: float(round(importances[i], 6))
        for i in np.argsort(importances)[::-1]
    }

    # 6. Save visual plots
    plot_and_save_confusion_matrix(cm, class_names, models_dir / CONFUSION_MATRIX_FILENAME)
    plot_and_save_feature_importance(importances, FEATURE_ORDER, models_dir / FEATURE_IMPORTANCE_FILENAME)

    # 7. Compile structured metrics dictionary
    metrics_data = {
        "dataset": "EngineFaultDB (Vergara et al., 2023)",
        "model_type": "RandomForestClassifier",
        "total_test_samples": int(len(y_test)),
        "overall_metrics": {
            "accuracy": round(acc, 6),
            "macro_f1": round(f1_macro, 6),
            "weighted_f1": round(f1_weighted, 6),
            "macro_precision": round(prec_macro, 6),
            "weighted_precision": round(prec_weighted, 6),
            "macro_recall": round(rec_macro, 6),
            "weighted_recall": round(rec_weighted, 6)
        },
        "per_class_metrics": {
            class_name: {
                "precision": round(report_dict[class_name]["precision"], 6),
                "recall": round(report_dict[class_name]["recall"], 6),
                "f1_score": round(report_dict[class_name]["f1-score"], 6),
                "support": int(report_dict[class_name]["support"])
            }
            for class_name in class_names
        },
        "confusion_matrix": cm.tolist(),
        "class_labels": {str(k): v for k, v in FAULT_LABELS.items()},
        "feature_importances": feat_importance_dict
    }

    # 8. Save metrics.json
    metrics_path = models_dir / METRICS_FILENAME
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_data, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")

    # 9. Print clean console review table
    print("\n" + "=" * 78)
    print(" " * 22 + "MODEL EVALUATION RESULTS (HELD-OUT TEST SET)")
    print("=" * 78)
    print(f"Overall Accuracy:       {acc * 100:6.2f}% ({acc:.4f})")
    print(f"Macro F1-Score:         {f1_macro:6.4f}")
    print(f"Weighted F1-Score:      {f1_weighted:6.4f}")
    print(f"Macro Precision:        {prec_macro:6.4f}")
    print(f"Macro Recall:           {rec_macro:6.4f}")
    print("-" * 78)
    print(f"{'Fault Class':<18} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'Test Support':<12}")
    print("-" * 78)
    for class_name in class_names:
        c_prec = report_dict[class_name]["precision"]
        c_rec = report_dict[class_name]["recall"]
        c_f1 = report_dict[class_name]["f1-score"]
        c_supp = int(report_dict[class_name]["support"])
        print(f"{class_name:<18} | {c_prec:8.4f}   | {c_rec:8.4f}   | {c_f1:8.4f}   | {c_supp:8,d}")
    print("=" * 78 + "\n")

    return metrics_data


if __name__ == "__main__":
    evaluate_model()
