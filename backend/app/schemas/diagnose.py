from pydantic import BaseModel


class DiagnoseRequest(BaseModel):
    MAP: float
    TPS: float
    Force: float
    Power: float
    RPM: float
    consumption_lh: float
    consumption_l100km: float
    Speed: float
    CO: float
    HC: float
    CO2: float
    O2: float
    Lambda: float
    AFR: float


class DiagnoseResponse(BaseModel):
    fault_type: int
    fault_name: str
    confidence: float
    class_probabilities: list[float]