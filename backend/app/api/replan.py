from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Assignment, Provider
from app.schemas.replan import ReplanRequest
from app.schemas.match import MatchResponse, MatchedProviderOut
from app.services.matching import find_candidates

router = APIRouter()


@router.post("/replan", response_model=MatchResponse)
def replan(request: ReplanRequest, db: Session = Depends(get_db)):
    assignment = (
        db.query(Assignment)
        .filter(Assignment.id == request.assignment_id)
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found",
        )

    if assignment.status != "assigned":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Assignment {assignment.id} is already "
                f"'{assignment.status}' and cannot be replanned again. "
                f"If a newer assignment exists, replan using its assignment_id instead."
            ),
        )

    failed_provider_id = assignment.provider_id

    failed_provider = (
        db.query(Provider)
        .filter(Provider.id == failed_provider_id)
        .first()
    )

    if failed_provider:
        failed_provider.is_available = True

    assignment.status = "failed"
    db.commit()

    candidates = find_candidates(
        db,
        required_capability=assignment.required_capability,
        vehicle_type=assignment.vehicle_type,
        latitude=assignment.latitude,
        longitude=assignment.longitude,
        exclude_provider_id=failed_provider_id,
    )

    if not candidates:
        return MatchResponse(
            matched=False,
            message="No alternative provider found.",
            assignment_id=None,
            assigned_provider=None,
            ranked_candidates=[],
        )

    ranked = [
        MatchedProviderOut(
            id=p.id,
            name=p.name,
            distance_km=round(dist, 2),
            rating=p.rating,
            score=round(score, 2),
        )
        for p, dist, score in candidates
    ]

    new_provider = candidates[0][0]
    new_provider.is_available = False

    new_assignment = Assignment(
        required_capability=assignment.required_capability,
        vehicle_type=assignment.vehicle_type,
        latitude=assignment.latitude,
        longitude=assignment.longitude,
        provider_id=new_provider.id,
        status="assigned",
    )

    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)

    return MatchResponse(
        matched=True,
        message=f"Reassigned to {new_provider.name}.",
        assignment_id=new_assignment.id,
        assigned_provider=ranked[0],
        ranked_candidates=ranked,
    )