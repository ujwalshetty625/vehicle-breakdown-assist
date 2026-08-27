from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Assignment
from app.schemas.diagnose import DiagnoseRequest
from app.schemas.match import MatchedProviderOut
from app.ml_integration.inference import predict_fault
from app.services.diagnosis import get_required_capability
from app.services.matching import find_candidates


from app.schemas.assist import AssistRequest


router = APIRouter()


@router.post("/assist")
def assist(
    request: AssistRequest,
    db: Session = Depends(get_db),
):
    # Fallback default coordinates (Bengaluru central) if 0/null
    lat = request.latitude if request.latitude and request.latitude != 0 else 12.9716
    lng = request.longitude if request.longitude and request.longitude != 0 else 77.5946
    v_type = request.vehicle_type or "car"

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

    # Evaluate symptoms to ensure fault title matches tire damage, battery failure, or engine issues accurately
    if request.symptoms:
        s_lower = request.symptoms.lower()
        if "tire" in s_lower or "tyre" in s_lower or "flat" in s_lower or "puncture" in s_lower or "wheel" in s_lower:
            diagnosis["fault_name"] = "Flat Tire / Puncture Damage"
            diagnosis["fault_type"] = 0
            diagnosis["confidence"] = 0.98
            diagnosis["class_probabilities"] = [0.98, 0.01, 0.00, 0.01]
        elif diagnosis["fault_name"] == "No Fault" or "battery" in s_lower or "smoke" in s_lower or "misfire" in s_lower:
            if "smoke" in s_lower or "misfire" in s_lower or "fuel" in s_lower or "power" in s_lower or "exhaust" in s_lower or "engine" in s_lower:
                diagnosis["fault_name"] = "Rich Mixture"
                diagnosis["fault_type"] = 1
                diagnosis["confidence"] = 0.96
                diagnosis["class_probabilities"] = [0.02, 0.96, 0.01, 0.01]
            elif "battery" in s_lower or "start" in s_lower or "click" in s_lower or "volt" in s_lower or "light" in s_lower:
                diagnosis["fault_name"] = "Low Voltage"
                diagnosis["fault_type"] = 3
                diagnosis["confidence"] = 0.92
                diagnosis["class_probabilities"] = [0.03, 0.02, 0.03, 0.92]
            elif "hesitat" in s_lower or "stall" in s_lower or "pop" in s_lower or "lean" in s_lower:
                diagnosis["fault_name"] = "Lean Mixture"
                diagnosis["fault_type"] = 2
                diagnosis["confidence"] = 0.94
                diagnosis["class_probabilities"] = [0.03, 0.01, 0.94, 0.02]

    # 3. Convert fault into recommended assistance
    required_capability = get_required_capability(
        diagnosis["fault_name"]
    )

    if required_capability is None and request.symptoms:
        s_lower = request.symptoms.lower()
        if "tire" in s_lower or "tyre" in s_lower or "flat" in s_lower or "puncture" in s_lower:
            required_capability = "tire_change"
        elif "tow" in s_lower:
            required_capability = "towing"
        elif "battery" in s_lower or "start" in s_lower or "jump" in s_lower:
            required_capability = "battery_jumpstart"
        else:
            required_capability = "engine_repair"

    # No roadside assistance required
    if required_capability is None:
        return {
            "diagnosis": diagnosis,
            "assistance_required": False,
            "required_capability": None,
            "matched": False,
            "message": "No immediate roadside assistance required based on diagnostic telemetry.",
            "assignment_id": None,
            "assigned_provider": None,
            "ranked_candidates": [],
        }

    # 4. Find eligible providers
    candidates = find_candidates(
        db,
        required_capability=required_capability,
        vehicle_type=v_type,
        latitude=lat,
        longitude=lng,
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
                f"{required_capability} and {v_type}."
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
            latitude=provider.latitude,
            longitude=provider.longitude,
            capabilities=[c.name for c in provider.capabilities],
            vehicle_types=[vt.name for vt in provider.vehicle_types],
        )
        for provider, distance, score in candidates
    ]

    # 6. Assign the best provider
    provider = candidates[0][0]

    provider.is_available = False

    assignment = Assignment(
        required_capability=required_capability,
        vehicle_type=v_type,
        latitude=lat,
        longitude=lng,
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