"""
preprocessing.py - Data loading, validation, stratified splitting, and feature scaling.

This module handles:
1. Downloading and loading the EngineFaultDB dataset.
2. Checking data integrity (missing values, types, duplicates, class distributions).
3. Splitting into train/test sets using Stratified sampling (80% train / 20% test).
4. Fitting StandardScaler strictly on training set features to avoid data leakage.
5. Saving and loading the fitted scaler artifact for offline evaluation and live inference.
"""

import os
import urllib.request
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Import feature definitions
import sys
# Allow imports when running as standalone script or as a module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from ml.src.features import FEATURE_ORDER, TARGET_COLUMN, FAULT_LABELS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
DEFAULT_DATASET_URL = "https://raw.githubusercontent.com/Leo-Thomas/EngineFaultDB/main/EngineFaultDB_Final.csv"
DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
DEFAULT_CSV_PATH = DEFAULT_DATA_DIR / "EngineFaultDB_Final.csv"
SCALER_FILENAME = "scaler.pkl"


def download_dataset(url: str = DEFAULT_DATASET_URL, target_path: Path = DEFAULT_CSV_PATH) -> Path:
    """
    Downloads EngineFaultDB CSV dataset if not already present locally.
    
    Args:
        url: Remote raw CSV URL.
        target_path: Local filesystem destination.
        
    Returns:
        Path to downloaded CSV file.
    """
    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if not target_path.exists():
        logger.info(f"Dataset not found at {target_path}. Downloading from {url}...")
        urllib.request.urlretrieve(url, str(target_path))
        logger.info(f"Successfully downloaded EngineFaultDB to {target_path}")
    else:
        logger.info(f"Dataset already exists at {target_path}")

    return target_path


def load_data(csv_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Loads EngineFaultDB CSV file into a pandas DataFrame and validates structure.

    Args:
        csv_path: Optional path to the CSV file. If None, uses DEFAULT_CSV_PATH.

    Returns:
        pd.DataFrame containing raw sensor readings and fault labels.
    """
    if csv_path is None:
        csv_path = DEFAULT_CSV_PATH

    csv_path = Path(csv_path)
    if not csv_path.exists():
        download_dataset(target_path=csv_path)

    logger.info(f"Loading dataset from {csv_path}...")
    df = pd.read_csv(csv_path)
    logger.info(f"Dataset loaded. Initial shape: {df.shape}")
    return df


def inspect_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Inspects dataset quality, schema types, missing values, and target distributions.
    Prints a formatted summary to console and returns metadata dictionary.

    Args:
        df: Input DataFrame.

    Returns:
        Dictionary containing summary statistics.
    """
    print("\n" + "=" * 70)
    print(" " * 20 + "DATASET INSPECTION REPORT")
    print("=" * 70)
    print(f"Total Rows:    {df.shape[0]:,}")
    print(f"Total Columns: {df.shape[1]}")
    
    # Missing values check
    missing_counts = df.isnull().sum()
    total_missing = missing_counts.sum()
    print(f"\nMissing Values Check (Total Nulls: {total_missing}):")
    if total_missing > 0:
        print(missing_counts[missing_counts > 0])
    else:
        print("  [OK] Zero missing / null entries detected.")

    # Target class distribution
    if TARGET_COLUMN in df.columns:
        print("\nTarget Class Distribution ('Fault'):")
        val_counts = df[TARGET_COLUMN].value_counts().sort_index()
        val_pcts = df[TARGET_COLUMN].value_counts(normalize=True).sort_index() * 100
        
        class_summary = {}
        for class_id, count in val_counts.items():
            label_name = FAULT_LABELS.get(int(class_id), f"Unknown ({class_id})")
            pct = val_pcts[class_id]
            print(f"  Class {class_id} ({label_name:<14}): {count:6,d} samples ({pct:5.2f}%)")
            class_summary[int(class_id)] = {
                "label": label_name,
                "count": int(count),
                "percentage": float(round(pct, 2))
            }
    else:
        class_summary = {}

    # Feature column verification
    print("\nFeature Columns Status against Frozen FEATURE_ORDER:")
    for feat in FEATURE_ORDER:
        present = feat in df.columns
        status = "[OK] PRESENT" if present else "[X] MISSING"
        dtype_str = str(df[feat].dtype) if present else "N/A"
        print(f"  {feat:<22} : {status} (dtype: {dtype_str})")

    print("=" * 70 + "\n")

    return {
        "shape": df.shape,
        "missing_count": int(total_missing),
        "class_summary": class_summary,
        "columns": df.columns.tolist()
    }


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw dataset by handling nulls, non-finite values, and invalid target classes.
    
    Design Decision Rationale:
    - For automotive sensor telemetry, corrupt/null rows represent lost sensor packets.
    - If missing or non-finite values occur, dropping them ensures the trained classifier
      never fits onto artifactual synthetic imputations.
    - If all rows are clean (0 nulls), dataset is returned untouched.

    Args:
        df: Raw DataFrame.

    Returns:
        Cleaned pd.DataFrame.
    """
    df_clean = df.copy()
    initial_len = len(df_clean)

    # 1. Drop exact duplicate rows (prevents train/test partition overlap)
    dup_count = df_clean.duplicated().sum()
    if dup_count > 0:
        df_clean = df_clean.drop_duplicates().reset_index(drop=True)
        logger.info(f"Data Cleaning: Removed {dup_count} exact duplicate rows.")

    # 2. Drop rows with nulls in any feature or target
    df_clean = df_clean.dropna(subset=FEATURE_ORDER + [TARGET_COLUMN])

    # 3. Drop rows with non-finite (infinite / NaN) values in numeric features
    numeric_features = [col for col in FEATURE_ORDER if col in df_clean.columns]
    is_finite_mask = np.isfinite(df_clean[numeric_features].values).all(axis=1)
    df_clean = df_clean[is_finite_mask]

    # 4. Ensure target is integer
    df_clean[TARGET_COLUMN] = df_clean[TARGET_COLUMN].astype(int)

    # 5. Filter target classes strictly to valid set {0, 1, 2, 3}
    valid_classes = set(FAULT_LABELS.keys())
    df_clean = df_clean[df_clean[TARGET_COLUMN].isin(valid_classes)]

    dropped_count = initial_len - len(df_clean)
    if dropped_count > 0:
        logger.info(
            f"Data Cleaning Summary: Total dropped rows = {dropped_count} "
            f"({dropped_count / initial_len:.4%}). Clean dataset: {len(df_clean):,} rows."
        )
    else:
        logger.info(f"Data Cleaning: All {len(df_clean)} rows are valid and complete.")

    return df_clean


def split_and_scale_data(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, StandardScaler]:
    """
    Splits features and target into stratified train/test sets and fits StandardScaler on train set.

    Design Decision Rationale:
    1. Stratified Split (80/20):
       Preserves class proportions across both partitions (Classes range ~19% - 29%).
    2. StandardScaler fitted ONLY on Training data:
       Prevents data leakage into the test evaluation partition. Test data is transformed
       using the training distribution mean and standard deviation.

    Args:
        df: Cleaned DataFrame with FEATURE_ORDER columns and TARGET_COLUMN.
        test_size: Proportion of dataset allocated to test set (default: 0.20 = 20%).
        random_state: Random seed for deterministic reproducibility (default: 42).

    Returns:
        Tuple of (X_train_scaled, X_test_scaled, y_train, y_test, scaler).
    """
    # Enforce strictly the frozen feature order
    X = df[FEATURE_ORDER].values.astype(np.float64)
    y = df[TARGET_COLUMN].values.astype(np.int64)

    # Stratified split to maintain balanced representation of all 4 fault modes
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y
    )

    logger.info(
        f"Data Partitioning completed: "
        f"Train samples = {len(y_train):,} ({1 - test_size:.0%}), "
        f"Test samples = {len(y_test):,} ({test_size:.0%})"
    )

    # Fit StandardScaler strictly on training features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    logger.info(
        f"Feature Scaling completed with StandardScaler (fitted on {X_train.shape[0]} training samples)."
    )

    return X_train_scaled, X_test_scaled, y_train, y_test, scaler


def save_scaler(scaler: StandardScaler, filepath: Optional[Path] = None) -> Path:
    """
    Serializes fitted StandardScaler to disk using joblib.

    Args:
        scaler: Fitted StandardScaler instance.
        filepath: Destination file path. If None, saves to DEFAULT_MODELS_DIR / SCALER_FILENAME.

    Returns:
        Path where scaler was saved.
    """
    if filepath is None:
        filepath = DEFAULT_MODELS_DIR / SCALER_FILENAME

    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, str(filepath))
    logger.info(f"Scaler saved successfully to: {filepath}")
    return filepath


def load_scaler(filepath: Optional[Path] = None) -> StandardScaler:
    """
    Loads serialized StandardScaler from disk.

    Args:
        filepath: Source file path. If None, loads from DEFAULT_MODELS_DIR / SCALER_FILENAME.

    Returns:
        Fitted StandardScaler instance ready for transform().
    """
    if filepath is None:
        filepath = DEFAULT_MODELS_DIR / SCALER_FILENAME

    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Scaler artifact not found at {filepath}. Run train.py or preprocessing.py first.")

    scaler = joblib.load(str(filepath))
    return scaler


def prepare_dataset(
    csv_path: Optional[Path] = None,
    models_dir: Optional[Path] = None,
    save_scaler_artifact: bool = True
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, StandardScaler, pd.DataFrame]:
    """
    End-to-end data preparation pipeline: download -> load -> clean -> split -> scale -> save scaler.

    Args:
        csv_path: Path to dataset CSV.
        models_dir: Path to directory for saving scaler.
        save_scaler_artifact: Whether to write scaler.pkl to disk.

    Returns:
        Tuple: (X_train_scaled, X_test_scaled, y_train, y_test, scaler, df_clean)
    """
    df_raw = load_data(csv_path)
    inspect_data(df_raw)
    df_clean = clean_data(df_raw)
    
    X_train_scaled, X_test_scaled, y_train, y_test, scaler = split_and_scale_data(
        df_clean,
        test_size=0.2,
        random_state=42
    )

    if save_scaler_artifact:
        save_dir = Path(models_dir) if models_dir else DEFAULT_MODELS_DIR
        save_scaler(scaler, save_dir / SCALER_FILENAME)

    return X_train_scaled, X_test_scaled, y_train, y_test, scaler, df_clean


if __name__ == "__main__":
    print("\n--- Running Preprocessing Pipeline Standalone ---")
    prepare_dataset()
    print("--- Preprocessing Complete ---\n")
