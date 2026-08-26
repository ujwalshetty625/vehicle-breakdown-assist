# Model Card: Engine Fault Diagnostic Classifier

**Project**: Intelligent Multimodal Vehicle Breakdown Assistance and Adaptive Recovery System  
**Model Name**: `engine-fault-rf-v1`  
**Artifact Files**: `ml/models/model.pkl`, `ml/models/scaler.pkl`, `ml/models/feature_order.json`, `ml/models/labels.json`  
**Date Trained**: August 2026  
**License & Source Dataset**: EngineFaultDB (Vergara et al., 2023, IEEE Access, DOI: [10.1109/ACCESS.2023.3331316](https://doi.org/10.1109/ACCESS.2023.3331316))  

---

## 1. Overview & Purpose

This machine learning model serves as the core diagnostic engine for automotive telemetry. It ingests 14 real-time vehicle sensor readings and classifies the operational engine state into one of 4 discrete fault modes to trigger appropriate roadside assistance and recovery workflows.

### Primary Intended Use
- Real-time diagnostic inference inside the backend API (FastAPI) upon receiving vehicle CAN bus / OBD-II telemetry packets.
- Identifying combustion mixture anomalies (Rich / Lean) and electrical power delivery degradation (Low Voltage).

---

## 2. Input Specification (API Contract)

The model expects a single vehicle telemetry sample containing **exactly 14 numeric features**. Feature order during inference is frozen to match `ml/models/feature_order.json`.

| Index | Feature Name (Canonical / Raw) | API Key Alias | Data Type | Physical Unit | Expected Range | Description |
|:---:|:---|:---|:---:|:---:|:---:|:---|
| 0 | `MAP` | `MAP` | `float` | kPa | 0.0 – 150.0 | Manifold Absolute Pressure |
| 1 | `TPS` | `TPS` | `float` | % | 0.0 – 100.0 | Throttle Position Sensor percentage |
| 2 | `Force` | `Force` | `float` | N | 0.0 – 5000.0 | Engine tractive / output force |
| 3 | `Power` | `Power` | `float` | kW | 0.0 – 300.0 | Engine output power |
| 4 | `RPM` | `RPM` | `float` | RPM | 0.0 – 8000.0 | Engine crankshaft revolutions per minute |
| 5 | `Consumption L/H` | `Fuel_consumption_LH` | `float` | L/H | 0.0 – 50.0 | Fuel consumption rate per hour |
| 6 | `Consumption L/100KM` | `Fuel_consumption_L100KM` | `float` | L/100KM | 0.0 – 50.0 | Fuel consumption rate per 100 kilometers |
| 7 | `Speed` | `Speed` | `float` | km/h | 0.0 – 250.0 | Vehicle road speed |
| 8 | `CO` | `CO` | `float` | % | 0.0 – 20.0 | Carbon Monoxide volumetric exhaust % |
| 9 | `HC` | `HC` | `float` | ppm | 0.0 – 5000.0 | Hydrocarbon exhaust emissions (ppm) |
| 10 | `CO2` | `CO2` | `float` | % | 0.0 – 25.0 | Carbon Dioxide volumetric exhaust % |
| 11 | `O2` | `O2` | `float` | % | 0.0 – 25.0 | Exhaust Oxygen volumetric % |
| 12 | `Lambda` | `Lambda` | `float` | ratio | 0.5 – 2.0 | Air-fuel equivalence ratio (1.0 = Stoichiometric) |
| 13 | `AFR` | `AFR` | `float` | ratio | 7.0 – 30.0 | Air-to-Fuel Ratio (14.7 = Stoichiometric gasoline) |

> **Note**: Both raw column names (`Consumption L/H`) and backend aliases (`Fuel_consumption_LH`) are supported by the reference prediction function.

---

## 3. Output Specification

The inference endpoint returns a structured dictionary:

```json
{
  "fault_type": 1,
  "fault_name": "Rich Mixture",
  "confidence": 0.985,
  "class_probabilities": {
    "No Fault": 0.005,
    "Rich Mixture": 0.985,
    "Lean Mixture": 0.005,
    "Low Voltage": 0.005
  },
  "status": "success"
}
```

### Label Mapping Table

| Fault Code (`fault_type`) | Diagnostic Name (`fault_name`) | System Meaning & Recommended Recovery Action |
|:---:|:---|:---|
| `0` | **No Fault** | Normal operation. No recovery action needed. |
| `1` | **Rich Mixture** | Excess fuel / insufficient air. Check MAF sensor, fuel pressure regulator, oxygen sensors, and air filters. |
| `2` | **Lean Mixture** | Excess air / insufficient fuel. Check for vacuum leaks, clogged fuel injectors, or failing fuel pump. |
| `3` | **Low Voltage** | Electrical system degradation. Check alternator output, battery state of charge, and electrical ground connections. |

---

## 4. Copy-Pasteable Inference Implementation (for FastAPI Backend)

Backend engineers can copy this self-contained class directly into `backend/app/services/ml_service.py`:

```python
import os
from pathlib import Path
from typing import Dict, Any, List
import joblib
import numpy as np

# Canonical feature ordering contract
FEATURE_ORDER: List[str] = [
    "MAP",
    "TPS",
    "Force",
    "Power",
    "RPM",
    "Consumption L/H",
    "Consumption L/100KM",
    "Speed",
    "CO",
    "HC",
    "CO2",
    "O2",
    "Lambda",
    "AFR",
]

FAULT_LABELS: Dict[int, str] = {
    0: "No Fault",
    1: "Rich Mixture",
    2: "Lean Mixture",
    3: "Low Voltage",
}


class EngineFaultPredictor:
    """
    Production inference handler for vehicle engine fault classification.
    Loads scaler and model once into memory for fast, thread-safe predictions.
    """

    def __init__(self, models_dir: str | Path = "ml/models"):
        models_path = Path(models_dir)
        model_file = models_path / "model.pkl"
        scaler_file = models_path / "scaler.pkl"

        if not model_file.exists() or not scaler_file.exists():
            raise FileNotFoundError(
                f"Missing ML model artifacts in {models_path}. Expected model.pkl and scaler.pkl."
            )

        self.model = joblib.load(str(model_file))
        self.scaler = joblib.load(str(scaler_file))
        self.class_names = [FAULT_LABELS[i] for i in range(len(FAULT_LABELS))]

    def _extract_and_order_features(self, telemetry: Dict[str, Any]) -> np.ndarray:
        """Extracts values in exact FEATURE_ORDER with alias handling."""
        ordered_values = []
        for feat in FEATURE_ORDER:
            if feat in telemetry:
                val = telemetry[feat]
            elif feat == "Consumption L/H" and "Fuel_consumption_LH" in telemetry:
                val = telemetry["Fuel_consumption_LH"]
            elif feat == "Consumption L/100KM" and "Fuel_consumption_L100KM" in telemetry:
                val = telemetry["Fuel_consumption_L100KM"]
            else:
                # Case-insensitive fallback
                matched_val = None
                for k, v in telemetry.items():
                    if k.strip().lower() == feat.lower():
                        matched_val = v
                        break
                if matched_val is None:
                    raise ValueError(f"Missing required sensor feature: '{feat}'")
                val = matched_val
            
            ordered_values.append(float(val))

        return np.array(ordered_values, dtype=np.float64).reshape(1, -1)

    def predict(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes fault classification inference on raw sensor telemetry dictionary.

        Args:
            telemetry: Dict containing the 14 sensor keys.

        Returns:
            Dict containing fault_type (int), fault_name (str),
            confidence (float), and class_probabilities (dict).
        """
        # 1. Extract & validate 14 ordered features
        raw_array = self._extract_and_order_features(telemetry)

        # 2. Standardize features using training scaler
        scaled_array = self.scaler.transform(raw_array)

        # 3. Predict class and probability distribution
        predicted_class_id = int(self.model.predict(scaled_array)[0])
        probabilities = self.model.predict_proba(scaled_array)[0]
        confidence = float(probabilities[predicted_class_id])

        class_prob_dict = {
            self.class_names[i]: float(round(probabilities[i], 4))
            for i in range(len(self.class_names))
        }

        return {
            "fault_type": predicted_class_id,
            "fault_name": FAULT_LABELS[predicted_class_id],
            "confidence": round(confidence, 4),
            "class_probabilities": class_prob_dict,
            "status": "success",
        }


# FastAPI Endpoint Example:
# from fastapi import FastAPI, HTTPException
# app = FastAPI()
# predictor = EngineFaultPredictor()
#
# @app.post("/api/diagnostics/classify")
# def classify_engine(telemetry: dict):
#     try:
#         return predictor.predict(telemetry)
#     except ValueError as e:
#         raise HTTPException(status_code=422, detail=str(e))
```

---

## 5. Verified Evaluation Metrics (Held-Out Test Set)

Evaluated on **11,200 stratified test samples** (20% held-out partition of the 55,999-row EngineFaultDB):

### Overall Performance

| Metric | Score | Percentage |
|:---|:---:|:---:|
| **Overall Accuracy** | `0.7440` | **74.40%** |
| **Macro F1-Score** | `0.7528` | **75.28%** |
| **Weighted F1-Score** | `0.7439` | **74.39%** |
| **Macro Precision** | `0.7534` | **75.34%** |
| **Macro Recall** | `0.7534` | **75.34%** |

### Per-Class Detailed Breakdown

| Fault Class | Precision | Recall | F1-Score | Test Set Support |
|:---|:---:|:---:|:---:|:---:|
| **No Fault** (0) | `1.0000` | `1.0000` | **`1.0000`** | 3,200 samples |
| **Rich Mixture** (1) | `1.0000` | `1.0000` | **`1.0000`** | 2,200 samples |
| **Lean Mixture** (2) | `0.5244` | `0.4773` | **`0.4997`** | 3,000 samples |
| **Low Voltage** (3) | `0.4891` | `0.5361` | **`0.5115`** | 2,800 samples |

### Top 5 Diagnostic Feature Importances (Gini Importance)
1. `CO` (Carbon Monoxide emissions): **12.36%**
2. `Force` (Engine Output Force): **10.58%**
3. `Consumption L/H` (Fuel Rate / Hour): **8.64%**
4. `HC` (Hydrocarbon emissions): **8.56%**
5. `Power` (Engine Output Power): **8.51%**

---

## 6. Known Limitations & Scope Boundaries

> [!WARNING]
> **Diagnostic Domain Boundary**:
> This machine learning model is exclusively trained to diagnose **internal engine, air-fuel mixture, and electrical voltage faults** (`No Fault`, `Rich Mixture`, `Lean Mixture`, and `Low Voltage`).
>
> It does **NOT** diagnose or detect:
> 1. **Tyre Failures** (e.g., punctures, low tire pressure TPMS alerts, blowouts).
> 2. **Cooling System Overheating** (e.g., coolant leaks, radiator fan failure).
> 3. **Mechanical Drivetrain / Transmission / Brake Failures**.
>
> In the overall "Intelligent Multimodal Vehicle Breakdown Assistance" architecture, non-engine breakdown scenarios (tyres, overheating, physical collisions) are governed by dedicated multimodal sensory pipelines and rule-based diagnostic services, **NOT** this model.
