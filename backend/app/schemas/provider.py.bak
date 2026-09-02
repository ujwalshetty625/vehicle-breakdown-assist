from pydantic import BaseModel

class ProviderOut(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    vehicle_types: list[str]
    is_available: bool
    rating: float
    capabilities: list[str]

    class Config:
        from_attributes = True  # lets Pydantic read SQLAlchemy objects directly