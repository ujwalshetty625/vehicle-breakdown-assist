from app.db.session import Base, engine, SessionLocal
from app.db.models import Provider, Capability

CAPABILITY_NAMES = ["towing", "battery_jumpstart", "tire_change", "engine_repair"]

DUMMY_PROVIDERS = [
    {"name": "Ravi Towing Co", "lat": 12.9716, "lng": 77.5946, "vehicle_types": "car,suv,truck", "caps": ["towing"]},
    {"name": "QuickFix Mechanics", "lat": 12.9352, "lng": 77.6146, "vehicle_types": "car,suv", "caps": ["battery_jumpstart", "tire_change"]},
    {"name": "Bangalore Auto Rescue", "lat": 12.9784, "lng": 77.6408, "vehicle_types": "car,suv,truck", "caps": ["towing", "engine_repair"]},
    {"name": "Speedy Tyre Point", "lat": 12.9611, "lng": 77.6387, "vehicle_types": "car", "caps": ["tire_change"]},
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        cap_lookup = {}
        for name in CAPABILITY_NAMES:
            cap = db.query(Capability).filter_by(name=name).first()
            if not cap:
                cap = Capability(name=name)
                db.add(cap)
                db.flush()
            cap_lookup[name] = cap

        for p in DUMMY_PROVIDERS:
            exists = db.query(Provider).filter_by(name=p["name"]).first()
            if exists:
                continue
            provider = Provider(
                name=p["name"],
                latitude=p["lat"],
                longitude=p["lng"],
                vehicle_types=p["vehicle_types"],
                is_available=True,
            )
            provider.capabilities = [cap_lookup[c] for c in p["caps"]]
            db.add(provider)

        db.commit()
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()