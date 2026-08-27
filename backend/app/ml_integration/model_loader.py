from pathlib import Path

import joblib


MODELS_DIR = (
    Path(__file__).resolve().parents[3]
    / "ml"
    / "models"
)


def load_model():
    model_path = MODELS_DIR / "model.pkl"

    if not model_path.exists():
        raise FileNotFoundError(
            f"ML model not found: {model_path}"
        )

    return joblib.load(model_path)


def load_scaler():
    scaler_path = MODELS_DIR / "scaler.pkl"

    if not scaler_path.exists():
        raise FileNotFoundError(
            f"ML scaler not found: {scaler_path}"
        )

    return joblib.load(scaler_path)