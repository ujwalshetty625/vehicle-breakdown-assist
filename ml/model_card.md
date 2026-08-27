# Model Card: Engine Fault Diagnostic Classifier (v2)

**Project**: Intelligent Multimodal Vehicle Breakdown Assistance and Adaptive Recovery System  
**Model Name**: `engine-fault-rf-v2`  
**Artifact Files**: `ml/models/model.pkl` (17.87 MB compressed), `ml/models/scaler.pkl`, `ml/models/feature_order.json`, `ml/models/labels.json`  
**Date Trained**: August 2026  
**License & Source Dataset**: EngineFaultDB (Vergara et al., 2023, IEEE Access, DOI: [10.1109/ACCESS.2023.3331316](https://doi.org/10.1109/ACCESS.2023.3331316))  

---

## 1. Overview & Purpose

This machine learning model serves as the primary diagnostic engine for vehicle engine telemetry. It ingests 14 real-time automotive sensor readings and classifies the operational engine state into one of 4 discrete fault modes to trigger appropriate roadside assistance and recovery workflows.

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
```

---

## 5. Verified Evaluation Metrics (Held-Out Test Set — v2)

Evaluated on **11,200 stratified test samples** (20% held-out partition of the deduplicated 55,998-row EngineFaultDB):

### Overall Performance

| Metric | Score | Percentage |
|:---|:---:|:---:|
| **Overall Accuracy** | `0.7476` | **74.76%** |
| **Macro F1-Score** | `0.7556` | **75.56%** |
| **Weighted F1-Score** | `0.7464` | **74.64%** |
| **Macro Precision** | `0.7576` | **75.76%** |
| **Macro Recall** | `0.7575` | **75.75%** |

### Per-Class Detailed Breakdown

| Fault Class | Precision | Recall | F1-Score | Test Set Support |
|:---|:---:|:---:|:---:|:---:|
| **No Fault** (0) | `1.0000` | `1.0000` | **`1.0000`** | 3,200 samples |
| **Rich Mixture** (1) | `1.0000` | `1.0000` | **`1.0000`** | 2,200 samples |
| **Lean Mixture** (2) | `0.5347` | `0.4447` | **`0.4855`** | 3,000 samples |
| **Low Voltage** (3) | `0.4959` | `0.5854` | **`0.5369`** | 2,800 samples |

### Top 5 Diagnostic Feature Importances (Gini Importance)
1. `CO` (Carbon Monoxide exhaust %): **13.77%**
2. `Force` (Engine Output Force): **10.71%**
3. `HC` (Hydrocarbon exhaust emissions): **8.59%**
4. `Consumption L/100KM` (Fuel Rate / 100km): **8.39%**
5. `Power` (Engine Output Power): **8.09%**

---

## 6. Changelog & Data Integrity Audit (v1 ➔ v2)

### Leakage Audit Findings
- An audit was conducted to verify whether the 1.0000 precision/recall in `No Fault` and `Rich Mixture` was an artifact of duplicate row leakage.
- **Result**: The dataset contains only **1 exact duplicate row (0.0018%)** out of 55,999 records (in Class 3).
- **Physical Explanation**:
  - `Rich Mixture` is linearly separated by extreme spikes in `HC` (up to 975 ppm) and `CO` (up to 10.13%), allowing decision trees to isolate it with 100% boundary certainty.
  - `No Fault` is cleanly bounded in baseline operating envelopes.
  - `Lean Mixture` and `Low Voltage` overlap because weak ignition voltage causes incomplete combustion misfires that generate exhaust telemetry identical to lean air-fuel mixtures.

### Changes Implemented in v2
1. **Deduplication**: Exact duplicate row removed during preprocessing (`55,998` clean samples).
2. **5-Fold Stratified Cross-Validation**: Validated hyperparameter stability across all folds.
3. **Hyperparameter Tuning**: Tuned `max_depth=25`, `n_estimators=200`, and `class_weight='balanced'` yielding improved Macro Recall (75.75%) and Accuracy (74.76%).
4. **Artifact Compression**: Serialized model with `joblib.dump(..., compress=3)`, compressing `model.pkl` from 163.35 MB down to **17.87 MB** for fast loading and GitHub compliance.

---

## 7. Known Limitations & Scope Boundaries

> [!WARNING]
> **Diagnostic Domain Boundary**:
> This machine learning model is exclusively trained to diagnose **internal engine, air-fuel mixture, and electrical voltage faults** (`No Fault`, `Rich Mixture`, `Lean Mixture`, and `Low Voltage`).
>
> **Sensor Telemetry Proxy Limitation**:
> `Lean Mixture` vs `Low Voltage` remains the hardest pair to separate because no sensor feature in the 14-channel telemetry directly measures electrical battery voltage or ignition coil primary voltage — combustion-side signals only act as an indirect proxy for it.
>
> The model does **NOT** diagnose or detect:
> 1. **Tyre Failures** (e.g., punctures, low tire pressure TPMS alerts, blowouts).
> 2. **Cooling System Overheating** (e.g., coolant leaks, radiator fan failure).
> 3. **Mechanical Drivetrain / Transmission / Brake Failures**.
>
> In the overall "Intelligent Multimodal Vehicle Breakdown Assistance" architecture, non-engine breakdown scenarios (tyres, overheating, physical collisions) are governed by dedicated multimodal sensory pipelines and rule-based diagnostic services, **NOT** this model.
