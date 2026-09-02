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
    query = db.query(Provider)
    if exclude_provider_id is not None:
        query = query.filter(Provider.id != exclude_provider_id)
    providers = query.all()

    if not providers:
        return []

    # Normalize raw vehicle type input
    raw_vt = (vehicle_type or "").lower()
    target_vt = "car"
    if any(k in raw_vt for k in ["motorcycle", "bike", "two_wheeler", "scooter", "moped"]):
        target_vt = "motorcycle"
    elif any(k in raw_vt for k in ["suv", "crossover", "4x4", "jeep"]):
        target_vt = "suv"
    elif any(k in raw_vt for k in ["auto", "rickshaw", "e-rickshaw", "3_wheeler"]):
        target_vt = "auto_rickshaw"
    elif any(k in raw_vt for k in ["truck", "mini_truck", "lorry", "pickup"]):
        target_vt = "truck"
    elif any(k in raw_vt for k in ["van", "minivan"]):
        target_vt = "van"

    VT_ALIASES = {
        "motorcycle": ["motorcycle", "scooter", "moped", "two_wheeler"],
        "car": ["car", "taxi", "suv", "sedan", "hatchback", "van", "coupe", "ev"],
        "suv": ["suv", "car", "truck", "pickup_truck"],
        "auto_rickshaw": ["auto_rickshaw", "e_rickshaw", "scooter", "car"],
        "van": ["van", "car", "suv", "mini_truck"],
        "truck": ["truck", "mini_truck", "light_truck", "heavy_truck", "suv"],
    }

    acceptable_types = set([target_vt])
    if target_vt in VT_ALIASES:
        acceptable_types.update(VT_ALIASES[target_vt])

    candidates = []
    fallback_capability_candidates = []
    all_distance_candidates = []

    req_cap = (required_capability or "").lower()

    for p in providers:
        capability_names = [c.name.lower() for c in p.capabilities]
        exact_capability = (not req_cap or req_cap in capability_names)
        has_capability = exact_capability or ("towing" in capability_names or "engine_repair" in capability_names)

        vehicle_type_names = set(vt.name.lower() for vt in p.vehicle_types)
        has_vehicle_match = bool(acceptable_types.intersection(vehicle_type_names))

        distance = haversine_km(latitude, longitude, p.latitude, p.longitude)
        score = score_provider(distance, p.rating)

        all_distance_candidates.append((p, distance, score + 10.0))

        if exact_capability and has_vehicle_match:
            candidates.append((p, distance, score))
        elif has_capability:
            fallback_capability_candidates.append((p, distance, score + 3.0))

    if candidates:
        final_list = candidates
    elif fallback_capability_candidates:
        final_list = fallback_capability_candidates
    else:
        final_list = all_distance_candidates

    final_list.sort(key=lambda c: c[2])
    return final_list