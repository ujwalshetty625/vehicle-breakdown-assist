from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Provider
from app.schemas.provider import ProviderOut

router = APIRouter()

@router.get("/providers", response_model=list[ProviderOut])
def list_providers(db: Session = Depends(get_db)):
    providers = db.query(Provider).all()
    result = []
    for p in providers:
        result.append(
            ProviderOut(
                id=p.id,
                name=p.name,
                latitude=p.latitude,
                longitude=p.longitude,
                vehicle_types=[vt.name for vt in p.vehicle_types],
                is_available=p.is_available,
                rating=p.rating,
                capabilities=[c.name for c in p.capabilities],
            )
        )
    return result