from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Assignment
from app.schemas.match import MatchedProviderOut
from app.schemas.assist import AssistRequest

from app.ml_integration.inference import predict_fault
from app.ml_integration.cv_inference import analyze_warning_light

from app.services.diagnosis import get_required_capability
from app.services.matching import find_candidates
from app.services.severity import assess_severity
from app.services.roadside_safety import assess_roadside_safety


router = APIRouter()


# Safety priority used only when high-confidence CV and telemetry
# indicate different assistance requirements.
CAPABILITY_PRIORITY = {
    "towing": 4,
    "engine_repair": 3,
    "battery_jumpstart": 2,
    "tire_change": 1,
}


def _select_multimodal_capability(
    telemetry_capability: str | None,
    cv_result: dict | None,
    symptoms: str | None,
) -> str | None:
    """
    Combine telemetry diagnosis and CV warning-light evidence.

    Rules:
    1. No CV image/result -> preserve existing telemetry behavior.
    2. Low-confidence CV -> ignore CV for capability routing.
    3. High-confidence CV + no telemetry capability -> use CV capability.
    4. High-confidence CV + telemetry capability:
       - If they agree, keep the capability.
       - If they disagree, choose the more safety-critical capability.
    5. Existing symptom fallback remains available if neither modality
       provides a capability.
    """

    # Existing behavior when no CV result exists.
    if not cv_result:
        return telemetry_capability

    cv_confidence = float(cv_result.get("confidence", 0.0))
    cv_capability = cv_result.get("recommended_capability")

    # Do not use uncertain CV predictions for provider routing.
    if cv_confidence < 0.65 or not cv_capability:
        return telemetry_capability

    # No telemetry capability — high-confidence CV can provide one.
    if telemetry_capability is None:
        return cv_capability

    # Both modalities agree.
    if telemetry_capability == cv_capability:
        return telemetry_capability

    # Conflict: choose the more safety-critical capability.
    telemetry_priority = CAPABILITY_PRIORITY.get(
        telemetry_capability,
        0,
    )
    cv_priority = CAPABILITY_PRIORITY.get(
        cv_capability,
        0,
    )

    if cv_priority > telemetry_priority:
        return cv_capability

    return telemetry_capability


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

    # =========================================================
    # 1. Prepare the 14 ML telemetry features
    # =========================================================

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

    # =========================================================
    # 2. Telemetry ML diagnosis
    # =========================================================

    # This remains the original trained ML model output.
    # It is never overwritten by the CV model.
    diagnosis = predict_fault(features)

    # =========================================================
    # 3. Computer Vision analysis
    # =========================================================

    cv_result = None

    if request.engine_photo:
        try:
            cv_result = analyze_warning_light(
                request.engine_photo
            )

        except ValueError as exc:
            # Invalid image data should not destroy the existing
            # telemetry-based assistance flow.
            cv_result = {
                "available": False,
                "error": str(exc),
            }

        except Exception as exc:
            # CV failure should degrade gracefully to telemetry ML.
            cv_result = {
                "available": False,
                "error": f"CV inference failed: {exc}",
            }

    # =========================================================
    # 4. Assess telemetry diagnosis severity
    # =========================================================

    severity_info = assess_severity(
        diagnosis["fault_name"],
        diagnosis["confidence"],
    )

    # =========================================================
    # 5. Determine capability from telemetry ML
    # =========================================================

    telemetry_capability = get_required_capability(
        diagnosis["fault_name"]
    )

    # =========================================================
    # 6. Combine telemetry + CV evidence
    # =========================================================

    required_capability = _select_multimodal_capability(
        telemetry_capability,
        cv_result if cv_result and cv_result.get("available", True) else None,
        request.symptoms,
    )

    # If the CV model is unavailable because of an error,
    # preserve the original telemetry capability.
    if cv_result and cv_result.get("available") is False:
        required_capability = telemetry_capability

    # =========================================================
    # 7. Existing symptom-based fallback
    # =========================================================

    # This remains the existing fallback for faults outside
    # the telemetry model's supported classes.
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

    # =========================================================
    # 8. No roadside assistance required
    # =========================================================

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
            "cv_analysis": cv_result,
            "severity": severity_info,
            "roadside_safety": roadside,
            "assistance_required": False,
            "required_capability": None,
            "matched": False,
            "message": (
                "No immediate roadside assistance required based on "
                "diagnostic telemetry and available visual analysis."
            ),
            "assignment_id": None,
            "assigned_provider": None,
            "ranked_candidates": [],
        }

    # =========================================================
    # 9. Find eligible providers
    # =========================================================

    candidates = find_candidates(
        db,
        required_capability=required_capability,
        vehicle_type=v_type,
        latitude=lat,
        longitude=lng,
    )

    # =========================================================
    # 10. Assistance required but no provider available
    # =========================================================

    if not candidates:
        roadside = assess_roadside_safety(
            severity=severity_info["severity"],
            safe_to_drive=severity_info["safe_to_drive"],
            distance_km=None,
            matched=False,
        )

        return {
            "diagnosis": diagnosis,
            "cv_analysis": cv_result,
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

    # =========================================================
    # 11. Build ranked provider response
    # =========================================================

    ranked = [
        MatchedProviderOut(
            id=provider.id,
            name=provider.name,
            phone=provider.phone,
            email=provider.email,
            distance_km=round(distance, 2),
            rating=provider.rating,
            score=round(score, 2),
            latitude=provider.latitude,
            longitude=provider.longitude,
            capabilities=[
                c.name for c in provider.capabilities
            ],
            vehicle_types=[
                vt.name for vt in provider.vehicle_types
            ],
        )
        for provider, distance, score in candidates
    ]

    # =========================================================
    # 12. Assign best provider
    # =========================================================

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

    # =========================================================
    # 13. Roadside safety assessment
    # =========================================================

    roadside = assess_roadside_safety(
        severity=severity_info["severity"],
        safe_to_drive=severity_info["safe_to_drive"],
        distance_km=ranked[0].distance_km,
        matched=True,
    )

    # =========================================================
    # 14. Final multimodal assistance response
    # =========================================================

    return {
        "diagnosis": diagnosis,
        "cv_analysis": cv_result,
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