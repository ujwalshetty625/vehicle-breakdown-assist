from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.match import MatchRequest, MatchResponse, MatchedProviderOut
from app.services.matching import find_candidates
from app.db.models import Assignment

router = APIRouter()


@router.post("/match-provider", response_model=MatchResponse)
def match_provider(request: MatchRequest, db: Session = Depends(get_db)):
    candidates = find_candidates(
        db,
        required_capability=request.required_capability,
        vehicle_type=request.vehicle_type,
        latitude=request.latitude,
        longitude=request.longitude,
    )

    if not candidates:
        return MatchResponse(
            matched=False,
            message="No available provider found for this capability/vehicle type.",
            assigned_provider=None,
            ranked_candidates=[],
        )

    ranked = [
        MatchedProviderOut(
            id=p.id, name=p.name, distance_km=round(dist, 2), rating=p.rating, score=round(score, 2)
        )
        for p, dist, score in candidates
    ]

    top_provider = candidates[0][0]
    top_provider.is_available = False

    assignment = Assignment(
        required_capability=request.required_capability,
        vehicle_type=request.vehicle_type,
        latitude=request.latitude,
        longitude=request.longitude,
        provider_id=top_provider.id,
        status="assigned",
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return MatchResponse(
        matched=True,
        message=f"Matched with {top_provider.name}.",
        assignment_id=assignment.id,
        assigned_provider=ranked[0],
        ranked_candidates=ranked,
    )