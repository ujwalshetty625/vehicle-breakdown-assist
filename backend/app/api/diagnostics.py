from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# Backend Database of Vehicle Diagnostic Telemetry Profiles from EngineFaultDB dataset
DIAGNOSTIC_PRESETS = [
    {
        "id": "preset_tire_damage",
        "name": "Flat Tire & Wheel Puncture Damage",
        "fault_name": "Flat Tire / Puncture Damage",
        "description": "TPMS sensor detects pressure loss in tire, wheel vibration reported.",
        "symptoms": "Flat tire on roadside, loss of tire pressure, wheel vibrating",
        "telemetry": {
            "MAP": 3.549,
            "TPS": 1.889,
            "Force": 7.428,
            "Power": 5.227,
            "RPM": 1192.77,
            "consumption_lh": 3.057,
            "consumption_l100km": 11.72,
            "Speed": 0.0,
            "CO": 0.46,
            "HC": 196.089,
            "CO2": 14.356,
            "O2": 1.08,
            "Lambda": 1.047,
            "AFR": 15.385
        }
    },
    {
        "id": "preset_rich_mixture",
        "name": "Engine Misfire & Fuel Injection Issue",
        "fault_name": "Rich Mixture",
        "description": "ECU reports excessive fuel ratio, dark exhaust smoke, high CO emissions and erratic engine revs.",
        "symptoms": "Heavy black smoke from exhaust, engine sputtering, strong fuel smell, loss of acceleration",
        "telemetry": {
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
            "AFR": 14.75
        }
    },
    {
        "id": "preset_low_voltage",
        "name": "Battery Dead & Low Alternator Voltage",
        "fault_name": "Low Voltage",
        "description": "ECU reports voltage drop under threshold, battery warning light active, starter click.",
        "symptoms": "Clicking noise on start, dim dashboard lights, radio cutting out, battery symbol illuminated",
        "telemetry": {
            "MAP": 1.685,
            "TPS": 0.983,
            "Force": 283.63,
            "Power": 3.236,
            "RPM": 1878.75,
            "consumption_lh": 3.202,
            "consumption_l100km": 7.952,
            "Speed": 40.384,
            "CO": 0.462,
            "HC": 214.24,
            "CO2": 12.971,
            "O2": 0.87,
            "Lambda": 1.04,
            "AFR": 15.284
        }
    },
    {
        "id": "preset_lean_mixture",
        "name": "Engine Hesitation & Vacuum Air Leak",
        "fault_name": "Lean Mixture",
        "description": "ECU reports insufficient fuel delivery, air intake leak, high emission readings.",
        "symptoms": "Car hesitates under acceleration, popping sound from intake, stalling at idle",
        "telemetry": {
            "MAP": 1.614,
            "TPS": 1.095,
            "Force": 78.864,
            "Power": 1.844,
            "RPM": 3566.67,
            "consumption_lh": 4.489,
            "consumption_l100km": 5.626,
            "Speed": 77.641,
            "CO": 0.722,
            "HC": 148.625,
            "CO2": 14.189,
            "O2": 1.119,
            "Lambda": 1.074,
            "AFR": 15.788
        }
    },
    {
        "id": "preset_normal",
        "name": "Standard Inspection (Normal Vehicle Health)",
        "fault_name": "No Fault",
        "description": "ECU operating parameters within normal manufacturer specifications.",
        "symptoms": "Routine checkup / minor noise investigation",
        "telemetry": {
            "MAP": 3.549,
            "TPS": 1.889,
            "Force": 7.428,
            "Power": 5.227,
            "RPM": 1192.77,
            "consumption_lh": 3.057,
            "consumption_l100km": 11.72,
            "Speed": 24.901,
            "CO": 0.46,
            "HC": 196.089,
            "CO2": 14.356,
            "O2": 1.08,
            "Lambda": 1.047,
            "AFR": 15.385
        }
    }
]


class ScanRequest(BaseModel):
    vehicle_model: Optional[str] = None
    vehicle_type: Optional[str] = "car"
    symptoms: Optional[str] = None


@router.get("/diagnostics/presets")
def get_diagnostic_presets():
    """Returns preset diagnostic telemetry profiles stored in backend database."""
    return DIAGNOSTIC_PRESETS


@router.get("/diagnostics/presets/{preset_id}")
def get_diagnostic_preset_by_id(preset_id: str):
    """Returns a single diagnostic telemetry preset by ID."""
    for preset in DIAGNOSTIC_PRESETS:
        if preset["id"] == preset_id:
            return preset
    return DIAGNOSTIC_PRESETS[0]


@router.post("/diagnostics/scan")
def auto_scan_vehicle_ecu(request: ScanRequest):
    """
    Simulates real OBD-II / ECU database vehicle diagnostic scanning.
    Analyzes symptoms & vehicle model to return fetched ECU telemetry from backend database.
    """
    symptoms_text = (request.symptoms or "").lower()

    if "tire" in symptoms_text or "tyre" in symptoms_text or "flat" in symptoms_text or "puncture" in symptoms_text or "wheel" in symptoms_text:
        selected = DIAGNOSTIC_PRESETS[0] # Flat Tire
    elif "battery" in symptoms_text or "light" in symptoms_text or "start" in symptoms_text or "volt" in symptoms_text or "dim" in symptoms_text:
        selected = DIAGNOSTIC_PRESETS[2] # Low Voltage
    elif "hesitat" in symptoms_text or "stall" in symptoms_text or "power" in symptoms_text or "lean" in symptoms_text:
        selected = DIAGNOSTIC_PRESETS[3] # Lean Mixture
    elif "smoke" in symptoms_text or "smell" in symptoms_text or "misfire" in symptoms_text or "rich" in symptoms_text or "overheat" in symptoms_text or "engine" in symptoms_text:
        selected = DIAGNOSTIC_PRESETS[1] # Rich Mixture
    else:
        selected = DIAGNOSTIC_PRESETS[1]

    return {
        "status": "success",
        "message": f"ECU Diagnostic Scan successful for {request.vehicle_model or 'Vehicle'}",
        "matched_preset": selected["name"],
        "fault_hypothesis": selected["fault_name"],
        "telemetry": selected["telemetry"],
    }
