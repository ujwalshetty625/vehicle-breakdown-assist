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

    target_vt = (vehicle_type or "").strip().lower()

    # Map vehicle type aliases to DB categories
    VT_ALIASES = {
        "motorcycle": ["motorcycle", "scooter", "moped", "two_wheeler"],
        "scooter": ["scooter", "motorcycle", "moped", "two_wheeler"],
        "moped": ["moped", "scooter", "motorcycle"],
        "auto_rickshaw": ["auto_rickshaw", "e_rickshaw", "scooter", "car"],
        "e_rickshaw": ["e_rickshaw", "auto_rickshaw", "scooter", "car"],
        "car": ["car", "taxi", "suv", "sedan", "hatchback", "van"],
        "taxi": ["taxi", "car", "suv"],
        "suv": ["suv", "car", "truck", "pickup_truck"],
        "van": ["van", "car", "suv", "mini_truck"],
        "truck": ["truck", "mini_truck", "light_truck", "heavy_truck", "suv"],
        "mini_truck": ["mini_truck", "truck", "light_truck", "pickup_truck", "car"],
        "light_truck": ["light_truck", "truck", "mini_truck", "heavy_truck"],
        "heavy_truck": ["heavy_truck", "truck", "tractor_trailer"],
        "pickup_truck": ["pickup_truck", "truck", "suv", "mini_truck"],
    }

    acceptable_types = set([target_vt])
    if target_vt in VT_ALIASES:
        acceptable_types.update(VT_ALIASES[target_vt])

    candidates = []
    fallback_candidates = []

    for p in providers:
        capability_names = [c.name.lower() for c in p.capabilities]
        has_capability = (
            not required_capability or required_capability.lower() in capability_names
        )

        vehicle_type_names = set(vt.name.lower() for vt in p.vehicle_types)
        has_vehicle_match = bool(acceptable_types.intersection(vehicle_type_names))

        distance = haversine_km(latitude, longitude, p.latitude, p.longitude)
        score = score_provider(distance, p.rating)

        if has_capability and has_vehicle_match:
            candidates.append((p, distance, score))
        elif has_capability:
            fallback_candidates.append((p, distance, score + 5.0)) # slight penalty for non-exact vehicle type match

    # If no strict vehicle match, use capability candidates
    final_list = candidates if candidates else fallback_candidates
    final_list.sort(key=lambda c: c[2])
    return final_list