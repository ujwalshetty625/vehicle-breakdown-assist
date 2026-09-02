from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import VehicleType

router = APIRouter()

VEHICLE_CATEGORIES = {
    "Two Wheeler": [
        {"id": "motorcycle", "name": "Motorcycle / Bike", "icon": "🏍️"},
        {"id": "scooter", "name": "Scooter / Scooty", "icon": "🛵"},
        {"id": "moped", "name": "Moped", "icon": "🛵"},
    ],
    "Auto & Light Commercial": [
        {"id": "auto_rickshaw", "name": "Auto Rickshaw", "icon": "🛺"},
        {"id": "e_rickshaw", "name": "E-Rickshaw", "icon": "🛺"},
        {"id": "taxi", "name": "Taxi / Cab", "icon": "🚕"},
        {"id": "van", "name": "Van / Minivan", "icon": "🚐"},
        {"id": "mini_truck", "name": "Mini Truck", "icon": "🛻"},
    ],
    "Passenger Vehicle": [
        {"id": "car", "name": "Sedan / Hatchback / Car", "icon": "🚗"},
        {"id": "suv", "name": "SUV / Crossover", "icon": "🚙"},
        {"id": "pickup_truck", "name": "Pickup Truck", "icon": "🛻"},
    ],
    "Commercial & Heavy": [
        {"id": "bus", "name": "Bus / Coach", "icon": "🚌"},
        {"id": "truck", "name": "Truck", "icon": "🚚"},
        {"id": "light_truck", "name": "Light Commercial Truck", "icon": "🚚"},
        {"id": "heavy_truck", "name": "Heavy Duty Truck", "icon": "🚛"},
        {"id": "tractor", "name": "Tractor", "icon": "🚜"},
        {"id": "tractor_trailer", "name": "Tractor Trailer", "icon": "🚛"},
        {"id": "construction_vehicle", "name": "Construction Vehicle", "icon": "🏗️"},
        {"id": "ambulance", "name": "Ambulance / Emergency", "icon": "🚑"},
    ],
}


@router.get("/vehicle-types")
def get_vehicle_types(db: Session = Depends(get_db)):
    db_types = db.query(VehicleType).all()
    db_type_names = set(vt.name for vt in db_types)

    # Build response format
    result = []
    for category, vehicles in VEHICLE_CATEGORIES.items():
        items = []
        for v in vehicles:
            items.append({
                "id": v["id"],
                "name": v["name"],
                "icon": v["icon"],
                "category": category,
                "in_db": v["id"] in db_type_names if db_type_names else True,
            })
        result.append({
            "category": category,
            "vehicles": items
        })

    # Return list of categories + flat list for convenience
    flat_list = [v for cat in result for v in cat["vehicles"]]
    return {
        "categories": result,
        "types": flat_list
    }
