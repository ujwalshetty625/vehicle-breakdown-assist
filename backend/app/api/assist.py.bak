from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Assignment
from app.schemas.match import MatchedProviderOut
from app.ml_integration.inference import predict_fault
from app.services.diagnosis import get_required_capability
from app.services.matching import find_candidates
from app.services.severity import assess_severity
from app.services.roadside_safety import assess_roadside_safety
from app.schemas.assist import AssistRequest


router = APIRouter()


@router.post("/assist")
def assist(
    request: AssistRequest,
    db: Session = Depends(get_db),
):
    lat = (
        request.latitude
        if request.latitude and request.latitude != 0
        else 12.9716
    )

    lng = (
        request.longitude
        if request.longitude and request.longitude != 0
        else 77.5946
    )

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

    # 2. Run ML diagnosis — this is the REAL model output, never overwritten
    diagnosis = predict_fault(features)

    # 3. Assess severity/safety from the real diagnosis
    severity_info = assess_severity(
        diagnosis["fault_name"],
        diagnosis["confidence"],
    )

    # 4. Convert fault into recommended assistance capability
    required_capability = get_required_capability(
        diagnosis["fault_name"]
    )

    # Rule-based fallback: only fires when ML found "No Fault" but symptoms suggest
    # something outside the ML model's scope (tires, towing) — never overwrites diagnosis.
    if required_capability is None and request.symptoms:
        s_lower = request.symptoms.lower()

        if (
            "tire" in s_lower
            or "tyre" in s_lower
            or "flat" in s_lower
            or "puncture" in s_lower
        ):
            required_capability = "tire_change"

        elif "tow" in s_lower:
            required_capability = "towing"

        elif (
            "battery" in s_lower
            or "start" in s_lower
            or "jump" in s_lower
        ):
            required_capability = "battery_jumpstart"

        else:
            required_capability = "engine_repair"

    # No roadside assistance required
    if required_capability is None:
        roadside = assess_roadside_safety(
            severity=severity_info["severity"],
            safe_to_drive=severity_info["safe_to_drive"],
            distance_km=None,
            matched=False,
            assistance_required=False,
        )

        return {
            "diagnosis": diagnosis,
            "severity": severity_info,
            "roadside_safety": roadside,
            "assistance_required": False,
            "required_capability": None,
            "matched": False,
            "message": (
                "No immediate roadside assistance required based on "
                "diagnostic telemetry."
            ),
            "assignment_id": None,
            "assigned_provider": None,
            "ranked_candidates": [],
        }

    # 5. Find eligible providers
    candidates = find_candidates(
        db,
        required_capability=required_capability,
        vehicle_type=v_type,
        latitude=lat,
        longitude=lng,
    )

    # Assistance required, but no provider currently available
    if not candidates:
        roadside = assess_roadside_safety(
            severity=severity_info["severity"],
            safe_to_drive=severity_info["safe_to_drive"],
            distance_km=None,
            matched=False,
        )

        return {
            "diagnosis": diagnosis,
            "severity": severity_info,
            "roadside_safety": roadside,
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

    # Roadside safety assessment for the matched provider
    roadside = assess_roadside_safety(
        severity=severity_info["severity"],
        safe_to_drive=severity_info["safe_to_drive"],
        distance_km=ranked[0].distance_km,
        matched=True,
    )

    return {
        "diagnosis": diagnosis,
        "severity": severity_info,
        "roadside_safety": roadside,
        "assistance_required": True,
        "required_capability": required_capability,
        "matched": True,
        "message": f"Matched with {provider.name}.",
        "assignment_id": assignment.id,
        "assigned_provider": ranked[0],
        "ranked_candidates": ranked,
    }