from typing import Optional
from pydantic import BaseModel


class AssistRequest(BaseModel):
    vehicle_type: str = "car"
    latitude: float = 12.9716
    longitude: float = 77.5946

    # 14 ML Telemetry fields required for fault diagnosis
    MAP: float = 35.2
    TPS: float = 12.5
    Force: float = 120.0
    Power: float = 80.0
    RPM: float = 2500.0
    consumption_lh: float = 2.5
    consumption_l100km: float = 8.5
    Speed: float = 60.0
    CO: float = 0.2
    HC: float = 100.0
    CO2: float = 14.5
    O2: float = 1.2
    Lambda: float = 1.0
    AFR: float = 14.7

    # Contextual vehicle & breakdown info
    vehicle_model: Optional[str] = None
    vehicle_year: Optional[str] = None
    fuel_type: Optional[str] = None
    symptoms: Optional[str] = None
    warning_light: Optional[str] = None
    location: Optional[str] = None
    diagnostic_preset_id: Optional[str] = None
    engine_photo: Optional[str] = None
