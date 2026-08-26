from pydantic import BaseModel

class MatchRequest(BaseModel):
    required_capability: str
    vehicle_type: str
    latitude: float
    longitude: float

class MatchedProviderOut(BaseModel):
    id: int
    name: str
    distance_km: float
    rating: float
    score: float

class MatchResponse(BaseModel):
    matched: bool
    message: str
    assignment_id: int | None = None
    assigned_provider: MatchedProviderOut | None
    ranked_candidates: list[MatchedProviderOut]

