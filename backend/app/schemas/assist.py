from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class AssistRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    vehicle_type: str = Field(default="car", alias="vehicleType")
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
    vehicle_model: Optional[str] = Field(default=None, alias="vehicleModel")
    vehicle_year: Optional[str] = Field(default=None, alias="vehicleYear")
    fuel_type: Optional[str] = Field(default=None, alias="fuelType")
    symptoms: Optional[str] = None
    warning_light: Optional[str] = Field(default=None, alias="warningLight")
    location: Optional[str] = None
    diagnostic_preset_id: Optional[str] = Field(default=None, alias="diagnosticPresetId")
    engine_photo: Optional[str] = Field(default=None, alias="enginePhoto")
