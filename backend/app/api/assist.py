from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Assignment
from app.schemas.diagnose import DiagnoseRequest
from app.schemas.match import MatchedProviderOut
from app.ml_integration.inference import predict_fault
from app.services.diagnosis import get_required_capability
from app.services.matching import find_candidates


router = APIRouter()


@router.post("/assist")
def assist(
    request: DiagnoseRequest,
    vehicle_type: str,
    latitude: float,
    longitude: float,
    db: Session = Depends(get_db),
):
    # 1. Prepare the 14 ML features
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

    # 2. Run ML diagnosis
    diagnosis = predict_fault(features)

    # 3. Convert fault into recommended assistance
    required_capability = get_required_capability(
        diagnosis["fault_name"]
    )

    # No roadside assistance required
    if required_capability is None:
        return {
            "diagnosis": diagnosis,
            "assistance_required": False,
            "required_capability": None,
            "matched": False,
            "message": "No roadside assistance required based on the diagnosis.",
            "assignment_id": None,
            "assigned_provider": None,
            "ranked_candidates": [],
        }

    # 4. Find eligible providers
    candidates = find_candidates(
        db,
        required_capability=required_capability,
        vehicle_type=vehicle_type,
        latitude=latitude,
        longitude=longitude,
    )

    # No suitable provider
    if not candidates:
        return {
            "diagnosis": diagnosis,
            "assistance_required": True,
            "required_capability": required_capability,
            "matched": False,
            "message": (
                "No available provider found for "
                f"{required_capability} and {vehicle_type}."
            ),
            "assignment_id": None,
            "assigned_provider": None,
            "ranked_candidates": [],
        }

    # 5. Build ranked provider list
    ranked = [
        MatchedProviderOut(
            id=provider.id,
            name=provider.name,
            distance_km=round(distance, 2),
            rating=provider.rating,
            score=round(score, 2),
        )
        for provider, distance, score in candidates
    ]

    # 6. Assign the best provider
    provider = candidates[0][0]

    provider.is_available = False

    assignment = Assignment(
        required_capability=required_capability,
        vehicle_type=vehicle_type,
        latitude=latitude,
        longitude=longitude,
        provider_id=provider.id,
        status="assigned",
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return {
        "diagnosis": diagnosis,
        "assistance_required": True,
        "required_capability": required_capability,
        "matched": True,
        "message": f"Matched with {provider.name}.",
        "assignment_id": assignment.id,
        "assigned_provider": ranked[0],
        "ranked_candidates": ranked,
    }