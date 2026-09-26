import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.diagnosis import (
    get_user_friendly_name,
    get_fault_description,
    get_fault_explanation,
    FAULT_USER_FRIENDLY_NAMES,
    FAULT_DESCRIPTIONS,
)
from app.ml_integration.inference import predict_fault


def test_exact_friendly_mappings_for_all_four_ml_classes():
    """
    Verify all four ML classes have the exact user-friendly interpretation:
    - No Fault: 'No issue detected'
    - Rich Mixture: 'Too much fuel in the engine'
    - Lean Mixture: 'Not enough fuel in the engine'
    - Low Voltage: 'Battery or electrical power issue'
    """
    expected = {
        "No Fault": (
            "No issue detected",
            "The available vehicle diagnostic data does not indicate a major fault.",
        ),
        "Rich Mixture": (
            "Too much fuel in the engine",
            "The engine appears to be receiving more fuel than required, which may affect performance and fuel efficiency.",
        ),
        "Lean Mixture": (
            "Not enough fuel in the engine",
            "The engine appears to be receiving less fuel than required, which may lead to poor performance or uneven engine operation.",
        ),
        "Low Voltage": (
            "Battery or electrical power issue",
            "The vehicle's electrical system is showing unusually low voltage, which may indicate a battery or charging-system problem.",
        ),
    }

    for fault_name, (expected_name, expected_desc) in expected.items():
        assert get_user_friendly_name(fault_name) == expected_name
        assert get_fault_description(fault_name) == expected_desc
        assert get_fault_explanation(fault_name) == expected_desc


def test_unexpected_fault_fallback_does_not_crash():
    """Unrecognized fault names return safe fallbacks and never crash."""
    name = get_user_friendly_name("Unknown Strange Error")
    desc = get_fault_description("Unknown Strange Error")
    assert "Unknown Strange Error" in name
    assert "operating anomaly" in desc
    assert len(desc) > 10


def test_predict_fault_returns_all_required_fields():
    """
    Inference response must preserve technical fields:
    - fault_type
    - fault_name
    - confidence
    - class_probabilities
    AND add:
    - user_friendly_name
    - description
    """
    features = {
        "MAP": 35.2,
        "TPS": 12.5,
        "Force": 120.0,
        "Power": 80.0,
        "RPM": 2500.0,
        "Consumption L/H": 2.5,
        "Consumption L/100KM": 8.5,
        "Speed": 60.0,
        "CO": 0.2,
        "HC": 100.0,
        "CO2": 14.5,
        "O2": 1.2,
        "Lambda": 1.0,
        "AFR": 14.7,
    }
    result = predict_fault(features)
    assert "fault_type" in result
    assert "fault_name" in result
    assert "confidence" in result
    assert "class_probabilities" in result
    assert "user_friendly_name" in result
    assert "description" in result

    assert result["user_friendly_name"] == get_user_friendly_name(result["fault_name"])
    assert result["description"] == get_fault_description(result["fault_name"])


def test_diagnose_api_returns_all_required_fields(client):
    """
    POST /diagnose must return 200 and include all technical and friendly fields:
    - fault_type
    - fault_name
    - confidence
    - class_probabilities
    - user_friendly_name
    - description
    """
    payload = {
        "MAP": 35.2,
        "TPS": 12.5,
        "Force": 120.0,
        "Power": 80.0,
        "RPM": 2500.0,
        "consumption_lh": 2.5,
        "consumption_l100km": 8.5,
        "Speed": 60.0,
        "CO": 0.2,
        "HC": 100.0,
        "CO2": 14.5,
        "O2": 1.2,
        "Lambda": 1.0,
        "AFR": 14.7,
    }
    response = client.post("/diagnose", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "fault_type" in data
    assert "fault_name" in data
    assert "confidence" in data
    assert "class_probabilities" in data
    assert "user_friendly_name" in data
    assert "description" in data
    assert data["user_friendly_name"] == get_user_friendly_name(data["fault_name"])
    assert data["description"] == get_fault_description(data["fault_name"])


def test_assist_api_diagnosis_contains_friendly_interpretation(client, seed_two_towing_providers):
    """POST /assist diagnosis block must include user_friendly_name and description."""
    payload = {
        "vehicle_type": "car",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "symptoms": "heavy black smoke from exhaust sputter",
        "MAP": 1.044,
        "TPS": 0.769,
        "Force": 80.04,
        "Power": 0.497,
        "RPM": 1188.55,
        "consumption_lh": 1.989,
        "consumption_l100km": 8.207,
        "Speed": 25.038,
        "CO": 1.925,
        "HC": 247.44,
        "CO2": 12.834,
        "O2": 0.56,
        "Lambda": 1.003,
        "AFR": 14.75,
    }
    response = client.post("/assist", json=payload)
    assert response.status_code == 200
    data = response.json()
    diag = data["diagnosis"]
    assert diag["fault_name"] == "Rich Mixture"
    assert diag["user_friendly_name"] == "Too much fuel in the engine"
    assert diag["description"] == "The engine appears to be receiving more fuel than required, which may affect performance and fuel efficiency."
