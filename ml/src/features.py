"""
features.py - Feature definitions, schema constants, and feature engineering utilities.

This module defines the canonical 14-feature schema and frozen feature ordering for the
EngineFaultDB automotive diagnostic classifier.

FROZEN FEATURE ORDER CONTRACT:
1.  MAP (kPa)
2.  TPS (%)
3.  Force (N)
4.  Power (kW)
5.  RPM
6.  Consumption L/H (L/H) / Fuel_consumption_LH
7.  Consumption L/100KM (L/100KM) / Fuel_consumption_L100KM
8.  Speed (km/h)
9.  CO (%)
10. HC (ppm)
11. CO2 (%)
12. O2 (%)
13. Lambda
14. AFR
"""

from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

# Canonical feature list matching the raw EngineFaultDB CSV headers in frozen order
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

# Canonical API / backend-friendly feature names (standardized identifier format)
API_FEATURE_NAMES: List[str] = [
    "MAP",
    "TPS",
    "Force",
    "Power",
    "RPM",
    "Fuel_consumption_LH",
    "Fuel_consumption_L100KM",
    "Speed",
    "CO",
    "HC",
    "CO2",
    "O2",
    "Lambda",
    "AFR",
]

# Mapping between backend API feature names and CSV raw column headers
API_TO_RAW_MAP: Dict[str, str] = {
    "MAP": "MAP",
    "TPS": "TPS",
    "Force": "Force",
    "Power": "Power",
    "RPM": "RPM",
    "Fuel_consumption_LH": "Consumption L/H",
    "Fuel_consumption_L100KM": "Consumption L/100KM",
    "Consumption L/H": "Consumption L/H",
    "Consumption L/100KM": "Consumption L/100KM",
    "Speed": "Speed",
    "CO": "CO",
    "HC": "HC",
    "CO2": "CO2",
    "O2": "O2",
    "Lambda": "Lambda",
    "AFR": "AFR",
}

RAW_TO_API_MAP: Dict[str, str] = {
    "Consumption L/H": "Fuel_consumption_LH",
    "Consumption L/100KM": "Fuel_consumption_L100KM",
}

# Target column name in raw dataset
TARGET_COLUMN: str = "Fault"

# Fault class label mapping (Integer -> Human-readable Diagnostic Name)
FAULT_LABELS: Dict[int, str] = {
    0: "No Fault",
    1: "Rich Mixture",
    2: "Lean Mixture",
    3: "Low Voltage",
}

# Detailed feature metadata including units, typical operating range, and descriptions
FEATURE_METADATA: Dict[str, Dict[str, Any]] = {
    "MAP": {
        "unit": "kPa",
        "description": "Manifold Absolute Pressure",
        "dtype": "float64",
        "min_expected": 0.0,
        "max_expected": 150.0,
    },
    "TPS": {
        "unit": "%",
        "description": "Throttle Position Sensor percentage",
        "dtype": "float64",
        "min_expected": 0.0,
        "max_expected": 100.0,
    },
    "Force": {
        "unit": "N",
        "description": "Engine output force / tractive force",
        "dtype": "float64",
        "min_expected": 0.0,
        "max_expected": 5000.0,
    },
    "Power": {
        "unit": "kW",
        "description": "Engine output power",
        "dtype": "float64",
        "min_expected": 0.0,
        "max_expected": 300.0,
    },
    "RPM": {
        "unit": "RPM",
        "description": "Engine crankshaft rotational speed",
        "dtype": "float64",
        "min_expected": 0.0,
        "max_expected": 8000.0,
    },
    "Consumption L/H": {
        "unit": "L/H",
        "description": "Fuel consumption rate per hour (Fuel_consumption_LH)",
        "dtype": "float64",
        "min_expected": 0.0,
        "max_expected": 50.0,
    },
    "Consumption L/100KM": {
        "unit": "L/100KM",
        "description": "Fuel consumption rate per 100 km (Fuel_consumption_L100KM)",
        "dtype": "float64",
        "min_expected": 0.0,
        "max_expected": 50.0,
    },
    "Speed": {
        "unit": "km/h",
        "description": "Vehicle road speed",
        "dtype": "float64",
        "min_expected": 0.0,
        "max_expected": 250.0,
    },
    "CO": {
        "unit": "%",
        "description": "Carbon Monoxide volumetric emission percentage",
        "dtype": "float64",
        "min_expected": 0.0,
        "max_expected": 20.0,
    },
    "HC": {
        "unit": "ppm",
        "description": "Hydrocarbon emission parts per million",
        "dtype": "float64",
        "min_expected": 0.0,
        "max_expected": 5000.0,
    },
    "CO2": {
        "unit": "%",
        "description": "Carbon Dioxide volumetric emission percentage",
        "dtype": "float64",
        "min_expected": 0.0,
        "max_expected": 25.0,
    },
    "O2": {
        "unit": "%",
        "description": "Exhaust Oxygen volumetric percentage",
        "dtype": "float64",
        "min_expected": 0.0,
        "max_expected": 25.0,
    },
    "Lambda": {
        "unit": "ratio",
        "description": "Air-fuel equivalence ratio (1.0 = stoichiometric)",
        "dtype": "float64",
        "min_expected": 0.5,
        "max_expected": 2.0,
    },
    "AFR": {
        "unit": "ratio",
        "description": "Air-to-Fuel Ratio (14.7 = stoichiometric gasoline)",
        "dtype": "float64",
        "min_expected": 7.0,
        "max_expected": 30.0,
    },
}


def normalize_feature_dict(sensor_dict: Dict[str, Any]) -> Dict[str, float]:
    """
    Normalizes input keys from either API format (e.g. Fuel_consumption_LH)
    or CSV header format (e.g. Consumption L/H) to the canonical FEATURE_ORDER keys.

    Args:
        sensor_dict: Dictionary containing the 14 sensor readings.

    Returns:
        Dictionary keyed by canonical FEATURE_ORDER strings with float values.

    Raises:
        ValueError: If any required feature is missing from sensor_dict.
    """
    normalized = {}
    for canonical_name in FEATURE_ORDER:
        # Check canonical name first
        if canonical_name in sensor_dict:
            val = sensor_dict[canonical_name]
        elif canonical_name == "Consumption L/H" and "Fuel_consumption_LH" in sensor_dict:
            val = sensor_dict["Fuel_consumption_LH"]
        elif canonical_name == "Consumption L/100KM" and "Fuel_consumption_L100KM" in sensor_dict:
            val = sensor_dict["Fuel_consumption_L100KM"]
        else:
            # Check case-insensitive / stripped match
            matched = False
            for k, v in sensor_dict.items():
                if k.strip().lower() == canonical_name.lower():
                    val = v
                    matched = True
                    break
            if not matched:
                raise ValueError(
                    f"Missing required feature '{canonical_name}'. "
                    f"Expected 14 features: {FEATURE_ORDER}"
                )
        
        try:
            normalized[canonical_name] = float(val)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Feature '{canonical_name}' must be numeric, got {val}: {e}")

    return normalized


def dict_to_ordered_array(sensor_dict: Dict[str, Any]) -> np.ndarray:
    """
    Converts a sensor dictionary into a 2D numpy array [1, 14] matching FEATURE_ORDER.

    Args:
        sensor_dict: Dictionary containing the 14 sensor features.

    Returns:
        2D numpy array of shape (1, 14).
    """
    normalized = normalize_feature_dict(sensor_dict)
    values = [normalized[feat] for feat in FEATURE_ORDER]
    return np.array(values, dtype=np.float64).reshape(1, -1)


def compute_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optional Feature Engineering Experiment:
    Computes domain-specific combustion, physics, and exhaust emission diagnostic features.

    NOTE: Baseline production model trains on raw 14 features to match API contract.
    This function is retained for exploratory and advanced experimentation.

    Derived features:
    1. Lambda_Deviation: Absolute deviation from stoichiometric lambda (|Lambda - 1.0|)
    2. AFR_Deviation: Deviation from stoichiometric AFR 14.7 (|AFR - 14.7|)
    3. CO_HC_Ratio: Incomplete combustion diagnostic ratio (CO / (HC + 1e-5))
    4. HC_O2_Ratio: Residual oxygen vs unburned hydrocarbon ratio (HC / (O2 + 1e-5))
    5. CO_CO2_Ratio: Combustion efficiency index (CO / (CO2 + 1e-5))
    6. Specific_Fuel_Consumption: Fuel per unit power (Consumption L/H / (Power + 1e-5))
    7. Throttle_MAP_Ratio: TPS to MAP volumetric efficiency proxy (TPS / (MAP + 1e-5))
    """
    df_feat = df.copy()

    lh_col = "Consumption L/H" if "Consumption L/H" in df_feat.columns else "Fuel_consumption_LH"

    if "Lambda" in df_feat.columns:
        df_feat["Lambda_Deviation"] = (df_feat["Lambda"] - 1.0).abs()

    if "AFR" in df_feat.columns:
        df_feat["AFR_Deviation"] = (df_feat["AFR"] - 14.7).abs()

    if "CO" in df_feat.columns and "HC" in df_feat.columns:
        df_feat["CO_HC_Ratio"] = df_feat["CO"] / (df_feat["HC"] + 1e-5)

    if "HC" in df_feat.columns and "O2" in df_feat.columns:
        df_feat["HC_O2_Ratio"] = df_feat["HC"] / (df_feat["O2"] + 1e-5)

    if "CO" in df_feat.columns and "CO2" in df_feat.columns:
        df_feat["CO_CO2_Ratio"] = df_feat["CO"] / (df_feat["CO2"] + 1e-5)

    if "Power" in df_feat.columns and lh_col in df_feat.columns:
        df_feat["Specific_Fuel_Consumption"] = df_feat[lh_col] / (df_feat["Power"] + 1e-5)

    if "TPS" in df_feat.columns and "MAP" in df_feat.columns:
        df_feat["Throttle_MAP_Ratio"] = df_feat["TPS"] / (df_feat["MAP"] + 1e-5)

    return df_feat
