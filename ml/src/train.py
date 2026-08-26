"""
train.py - Model training, cross-validation tuning, and artifact serialization.

This script:
1. Loads and prepares stratified training/testing data via preprocessing.py.
2. Compares multiple Random Forest configurations using 5-fold Stratified Cross-Validation (Macro F1).
3. Trains the champion model on the full training partition.
4. Serializes the trained model artifact to ml/models/model.pkl.
5. Exports feature ordering (feature_order.json) and class label mappings (labels.json).
6. Outputs a comprehensive training summary to console.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score

# Allow imports when running as standalone script or as a module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from ml.src.features import FEATURE_ORDER, FAULT_LABELS
from ml.src.preprocessing import prepare_dataset, DEFAULT_MODELS_DIR, DEFAULT_DATA_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

MODEL_FILENAME = "model.pkl"
FEATURE_ORDER_FILENAME = "feature_order.json"
LABELS_FILENAME = "labels.json"


def evaluate_candidate_models(
    X_train: np.ndarray,
    y_train: np.ndarray,
    cv_folds: int = 5,
    random_state: int = 42
) -> Tuple[RandomForestClassifier, Dict[str, Any], List[Dict[str, Any]]]:
    """
    Evaluates candidate RandomForest configurations via Stratified K-Fold Cross-Validation.
    Selects the best model configuration based on Macro F1 score.

    Args:
        X_train: Standardized training features.
        y_train: Training class labels.
        cv_folds: Number of stratified folds (default: 5).
        random_state: Seed for reproducibility.

    Returns:
        Tuple: (champion_model_instance, best_config_dict, comparison_results_list)
    """
    candidate_configs = [
        {
            "name": "RF_Config_1 (Fast Baseline)",
            "params": {
                "n_estimators": 100,
                "max_depth": 15,
                "min_samples_split": 5,
                "class_weight": "balanced",
                "random_state": random_state,
                "n_jobs": -1
            }
        },
        {
            "name": "RF_Config_2 (Recommended Deep)",
            "params": {
                "n_estimators": 200,
                "max_depth": None,
                "min_samples_split": 2,
                "class_weight": "balanced",
                "random_state": random_state,
                "n_jobs": -1
            }
        },
        {
            "name": "RF_Config_3 (High Capacity)",
            "params": {
                "n_estimators": 300,
                "max_depth": 25,
                "min_samples_split": 2,
                "class_weight": "balanced",
                "random_state": random_state,
                "n_jobs": -1
            }
        }
    ]

    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    comparison_results = []
    best_f1 = -1.0
    best_config = candidate_configs[0]
    best_model = None

    print("\n" + "=" * 75)
    print(" " * 18 + f"STRATIFIED {cv_folds}-FOLD CROSS-VALIDATION")
    print("=" * 75)
    print(f"{'Configuration Name':<32} | {'Macro F1 (Mean +/- Std)':<22} | {'Accuracy (Mean)':<15}")
    print("-" * 75)

    for candidate in candidate_configs:
        model = RandomForestClassifier(**candidate["params"])
        
        # Cross-validation scores for Macro F1 (class imbalance sensitive)
        f1_scores = cross_val_score(model, X_train, y_train, cv=skf, scoring="f1_macro", n_jobs=-1)
        acc_scores = cross_val_score(model, X_train, y_train, cv=skf, scoring="accuracy", n_jobs=-1)
        
        mean_f1 = float(np.mean(f1_scores))
        std_f1 = float(np.std(f1_scores))
        mean_acc = float(np.mean(acc_scores))

        result_entry = {
            "name": candidate["name"],
            "params": candidate["params"],
            "mean_macro_f1": mean_f1,
            "std_macro_f1": std_f1,
            "mean_accuracy": mean_acc
        }
        comparison_results.append(result_entry)

        print(f"{candidate['name']:<32} | {mean_f1:6.4f} +/- {std_f1:6.4f}     | {mean_acc:6.4f}")

        if mean_f1 > best_f1:
            best_f1 = mean_f1
            best_config = candidate
            best_model = model

    print("=" * 75)
    print(f"[CHAMPION] Selected Champion: {best_config['name']} with Macro F1 = {best_f1:.4f}\n")

    return best_model, best_config, comparison_results


def train_champion_model(
    model: RandomForestClassifier,
    X_train: np.ndarray,
    y_train: np.ndarray
) -> RandomForestClassifier:
    """
    Fits the selected champion estimator on the full training dataset.

    Args:
        model: Unfitted or template RandomForestClassifier.
        X_train: Standardized training features.
        y_train: Training labels.

    Returns:
        Fitted RandomForestClassifier.
    """
    logger.info(f"Training champion model on all {X_train.shape[0]:,} training samples...")
    model.fit(X_train, y_train)
    logger.info("Champion model training completed successfully.")
    return model


def save_training_artifacts(
    model: RandomForestClassifier,
    best_config: Dict[str, Any],
    models_dir: Path = DEFAULT_MODELS_DIR
) -> Dict[str, Path]:
    """
    Saves model weights, feature order schema, and label mappings.

    Args:
        model: Fitted RandomForestClassifier.
        best_config: Hyperparameter dictionary of the champion model.
        models_dir: Output directory path.

    Returns:
        Dictionary of saved file paths.
    """
    models_dir = Path(models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save model weights (compressed with joblib compress=3 for lightweight git & memory transfer)
    model_path = models_dir / MODEL_FILENAME
    joblib.dump(model, str(model_path), compress=3)
    logger.info(f"Model saved to: {model_path} (compressed size: {os.path.getsize(model_path) / (1024*1024):.2f} MB)")

    # 2. Save feature order contract
    feature_order_path = models_dir / FEATURE_ORDER_FILENAME
    with open(feature_order_path, "w", encoding="utf-8") as f:
        json.dump(FEATURE_ORDER, f, indent=2)
    logger.info(f"Feature order contract saved to: {feature_order_path}")

    # 3. Save labels mapping
    labels_path = models_dir / LABELS_FILENAME
    labels_dict = {str(k): v for k, v in FAULT_LABELS.items()}
    with open(labels_path, "w", encoding="utf-8") as f:
        json.dump(labels_dict, f, indent=2)
    logger.info(f"Label mappings saved to: {labels_path}")

    return {
        "model": model_path,
        "feature_order": feature_order_path,
        "labels": labels_path
    }


def print_training_summary(
    model: RandomForestClassifier,
    X_train: np.ndarray,
    X_test: np.ndarray,
    best_config: Dict[str, Any]
) -> None:
    """
    Prints a clean, professional console training report with feature importances.
    """
    print("\n" + "=" * 70)
    print(" " * 22 + "MODEL TRAINING SUMMARY")
    print("=" * 70)
    print(f"Algorithm:           RandomForestClassifier")
    print(f"Training Samples:    {X_train.shape[0]:,}")
    print(f"Testing Samples:     {X_test.shape[0]:,}")
    print(f"Input Features:      {X_train.shape[1]}")
    print(f"Target Classes:      {len(FAULT_LABELS)} {list(FAULT_LABELS.values())}")
    print("\nSelected Hyperparameters:")
    for k, v in best_config["params"].items():
        print(f"  - {k:<20}: {v}")

    # Feature Importances
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    print("\nFeature Importances (Gini Importance):")
    for rank, idx in enumerate(indices, 1):
        feat_name = FEATURE_ORDER[idx]
        imp_val = importances[idx]
        bar = "#" * int(imp_val * 50)
        print(f"  {rank:2d}. {feat_name:<22} : {imp_val:6.4f} ({imp_val*100:5.2f}%) {bar}")
    print("=" * 70 + "\n")


def run_training_pipeline() -> Tuple[RandomForestClassifier, Dict[str, Any]]:
    """
    Orchestrates the complete training workflow.
    """
    logger.info("Initializing ML Training Pipeline...")
    
    # 1. Prepare data
    X_train, X_test, y_train, y_test, scaler, df_clean = prepare_dataset()

    # 2. Evaluate candidate configs
    champion_template, best_config, cv_results = evaluate_candidate_models(X_train, y_train)

    # 3. Train champion on full training set
    champion_model = train_champion_model(champion_template, X_train, y_train)

    # 4. Save artifacts
    save_training_artifacts(champion_model, best_config)

    # 5. Print summary
    print_training_summary(champion_model, X_train, X_test, best_config)

    return champion_model, best_config


if __name__ == "__main__":
    run_training_pipeline()
