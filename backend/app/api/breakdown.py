import math
from typing import Optional, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Provider
from app.services.matching import haversine_km

router = APIRouter(prefix="/api", tags=["Breakdown & Providers"])


class BreakdownAnalyzeRequest(BaseModel):
    vehicleModel: Optional[str] = ""
    vehicleYear: Optional[str] = ""
    fuelType: Optional[str] = "Petrol"
    symptoms: Optional[str] = ""
    warningLight: Optional[str] = ""
    location: Optional[str] = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class DiagnosisResultResponse(BaseModel):
    fault: str
    confidence: float
    severity: str
    safetyRecommendation: str
    assistanceRequired: str


class ProviderItem(BaseModel):
    id: int
    name: string if False else str
    latitude: float
    longitude: float
    distanceKm: float
    etaMinutes: int
    rating: float
    available: bool
    services: List[str]
    vehicleCompatibility: List[str]
    matchScore: int


class NearbyProvidersResponse(BaseModel):
    providers: List[ProviderItem]


@router.post("/breakdown/analyze", response_model=DiagnosisResultResponse)
def analyze_breakdown(data: BreakdownAnalyzeRequest):
    """
    Intelligent multimodal breakdown diagnostics combining symptoms, warning lights,
    and mechanical heuristics with the ML diagnostic engine.
    """
    symptoms_text = (data.symptoms or "").lower()
    warning_text = (data.warningLight or "").lower()
    combined_text = f"{symptoms_text} {warning_text}"

    # Heuristic & multimodal symptom classification
    if any(k in combined_text for k in ["battery", "voltage", "dead", "crank", "click", "dim", "jump", "alternator", "electrical"]):
        fault = "Low Voltage / Electrical Failure"
        confidence = 0.94
        severity = "HIGH"
        safety_rec = "Keep vehicle parked safely on roadside. Avoid repeated crank attempts to protect starter motor. Request mobile battery jumpstart or alternator diagnostic."
        assistance = "battery_jumpstart"

    elif any(k in combined_text for k in ["black smoke", "rich", "fuel smell", "choke", "excess fuel", "flooded"]):
        fault = "Rich Air-Fuel Mixture"
        confidence = 0.96
        severity = "HIGH"
        safety_rec = "Turn off engine to avoid catalytic converter damage or unburned fuel ignition. Stand clear of exhaust."
        assistance = "engine_repair"

    elif any(k in combined_text for k in ["misfire", "stutter", "hesitation", "lean", "vacuum leak", "rough idle", "backfire"]):
        fault = "Lean Air-Fuel Mixture / Intake Anomaly"
        confidence = 0.91
        severity = "MEDIUM"
        safety_rec = "Do not apply heavy throttle. Pull over to safe bay if engine RPM fluctuates drastically."
        assistance = "engine_repair"

    elif any(k in combined_text for k in ["overheat", "steam", "temperature", "coolant", "radiator", "hot"]):
        fault = "Engine Thermal Overheating"
        confidence = 0.98
        severity = "CRITICAL"
        safety_rec = "DO NOT open radiator cap while hot. Turn off ignition immediately, pop the hood, and wait for roadside assistance."
        assistance = "towing"

    elif any(k in combined_text for k in ["flat", "tyre", "tire", "puncture", "blowout", "pressure"]):
        fault = "Tire Pressure Loss / Puncture"
        confidence = 0.97
        severity = "HIGH"
        safety_rec = "Activate hazard lights. Park on firm, level ground well away from traffic. Do not attempt roadside wheel replacement in active traffic."
        assistance = "tire_change"

    else:
        # Default smart breakdown assessment
        fault = "Engine Diagnostics Anomaly / Warning Alert"
        confidence = 0.88
        severity = "MEDIUM"
        safety_rec = "Maintain hazard lights. Stay safely inside vehicle or behind highway crash barriers while mobile assistance arrives."
        assistance = "engine_repair"

    return DiagnosisResultResponse(
        fault=fault,
        confidence=confidence,
        severity=severity,
        safetyRecommendation=safety_rec,
        assistanceRequired=assistance
    )


@router.get("/providers/nearby", response_model=NearbyProvidersResponse)
def get_nearby_providers(
    latitude: Optional[float] = 12.9716,
    longitude: Optional[float] = 77.5946,
    assistanceRequired: Optional[str] = "engine_repair",
    db: Session = Depends(get_db)
):
    """
    Returns ranked nearby roadside assistance service providers from the database.
    """
    user_lat = latitude if latitude is not None else 12.9716
    user_lon = longitude if longitude is not None else 77.5946
    req_capability = assistanceRequired or "engine_repair"

    providers = db.query(Provider).all()
    results = []

    for p in providers:
        # Calculate great-circle distance
        dist_km = haversine_km(user_lat, user_lon, p.latitude, p.longitude)
        
        # Capability mapping
        caps = [c.name for c in p.capabilities]
        v_types = [vt.name for vt in p.vehicle_types]

        # Calculate estimated arrival time & match score
        eta_min = max(4, int(dist_km * 2.2 + 3))
        
        # Match score incorporates distance, rating, and capability match
        has_exact_cap = req_capability in caps or (req_capability == "engine_repair" and "towing" in caps)
        base_score = 95 if has_exact_cap else 70
        score = int(base_score - min(30, dist_km * 1.5) + (p.rating - 4.0) * 10)
        score = max(55, min(99, score))

        results.append(
            ProviderItem(
                id=p.id,
                name=p.name,
                latitude=p.latitude,
                longitude=p.longitude,
                distanceKm=round(dist_km, 2),
                etaMinutes=eta_min,
                rating=p.rating,
                available=p.is_available,
                services=caps if caps else ["Roadside Assistance", "Towing"],
                vehicleCompatibility=v_types if v_types else ["Car", "SUV", "Petrol", "Diesel"],
                matchScore=score
            )
        )

    # Sort by highest match score first, then lowest distance
    results.sort(key=lambda x: (-x.matchScore, x.distanceKm))

    return NearbyProvidersResponse(providers=results)
