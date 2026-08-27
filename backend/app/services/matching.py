import math
from sqlalchemy.orm import Session
from app.db.models import Provider

RATING_WEIGHT = 2.0  # each rating point (0-5) "worth" 2 km of distance saved


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/lng points, in kilometers."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def score_provider(distance_km: float, rating: float) -> float:
    """Lower score = better. Distance penalizes, rating rewards."""
    return distance_km - (rating * RATING_WEIGHT)


def find_candidates(
    db: Session,
    required_capability: str,
    vehicle_type: str,
    latitude: float,
    longitude: float,
    exclude_provider_id: int | None = None,
):
    """
    Returns a list of (provider, distance_km, score) tuples,
    filtered by availability + capability + vehicle type, sorted best-first.
    exclude_provider_id lets /replan skip a provider that already failed for this breakdown.
    """
    query = db.query(Provider).filter(Provider.is_available == True)  # noqa: E712
    if exclude_provider_id is not None:
        query = query.filter(Provider.id != exclude_provider_id)
    providers = query.all()

    candidates = []
    for p in providers:
        capability_names = [c.name for c in p.capabilities]
        if required_capability not in capability_names:
            continue
        vehicle_type_names = [vt.name for vt in p.vehicle_types]
        if vehicle_type not in vehicle_type_names:
            continue

        distance = haversine_km(latitude, longitude, p.latitude, p.longitude)
        score = score_provider(distance, p.rating)
        candidates.append((p, distance, score))

    candidates.sort(key=lambda c: c[2])
    return candidates