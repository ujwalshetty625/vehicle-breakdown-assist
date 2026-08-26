from fastapi import APIRouter

from app.schemas.diagnose import DiagnoseRequest, DiagnoseResponse
from app.ml_integration.inference import predict_fault

router = APIRouter()


@router.post("/diagnose", response_model=DiagnoseResponse)
def diagnose(request: DiagnoseRequest):
    features = {
        "MAP": request.MAP,
        "TPS": request.TPS,
        "Force": request.Force,
        "Power": request.Power,
        "RPM": request.RPM,
        "Consumption L/H": request.consumption_lh,
        "Consumption L/100KM": request.consumption_l100km,
        "Speed": request.Speed,
        "CO": request.CO,
        "HC": request.HC,
        "CO2": request.CO2,
        "O2": request.O2,
        "Lambda": request.Lambda,
        "AFR": request.AFR,
    }

    result = predict_fault(features)

    return DiagnoseResponse(**result)