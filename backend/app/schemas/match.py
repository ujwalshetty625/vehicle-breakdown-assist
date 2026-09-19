from pydantic import BaseModel, Field


class MatchRequest(BaseModel):
    required_capability: str
    vehicle_type: str
    latitude: float
    longitude: float


class MatchedProviderOut(BaseModel):
    id: int
    name: str
    phone: str | None = None
    email: str | None = None
    distance_km: float
    rating: float
    score: float
    latitude: float = 0.0
    longitude: float = 0.0

    capabilities: list[str] = Field(default_factory=list)
    vehicle_types: list[str] = Field(default_factory=list)


class MatchResponse(BaseModel):
    matched: bool
    message: str
    assignment_id: int | None = None
    assigned_provider: MatchedProviderOut | None
    ranked_candidates: list[MatchedProviderOut]