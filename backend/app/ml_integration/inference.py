import json
from pathlib import Path

import numpy as np

from app.ml_integration.model_loader import load_model, load_scaler
from app.services.diagnosis import (
    get_user_friendly_name,
    get_fault_description,
    get_fault_explanation,
)


MODELS_DIR = (
    Path(__file__).resolve().parents[3]
    / "ml"
    / "models"
)

with open(MODELS_DIR / "feature_order.json", "r") as f:
    FEATURE_ORDER = json.load(f)

with open(MODELS_DIR / "labels.json", "r") as f:
    LABELS = json.load(f)


model = load_model()
scaler = load_scaler()


def predict_fault(features: dict[str, float]):
    values = [features[name] for name in FEATURE_ORDER]

    X = np.array([values], dtype=float)

    X_scaled = scaler.transform(X)

    prediction = model.predict(X_scaled)[0]
    probabilities = model.predict_proba(X_scaled)[0]

    fault_type = int(prediction)
    confidence = float(probabilities[fault_type])
    fault_name = LABELS[str(fault_type)]
    user_friendly_name = get_user_friendly_name(fault_name)
    description = get_fault_description(fault_name)

    return {
        "fault_type": fault_type,
        "fault_name": fault_name,
        "user_friendly_name": user_friendly_name,
        "description": description,
        "explanation": description,
        "user_friendly_explanation": description,
        "confidence": round(confidence, 4),
        "class_probabilities": [
            round(float(probability), 4)
            for probability in probabilities
        ],
    }