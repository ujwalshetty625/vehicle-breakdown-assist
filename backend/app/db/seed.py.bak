from app.db.session import Base, engine, SessionLocal
from app.db.models import Provider, Capability, VehicleType


CAPABILITY_NAMES = [
    "towing",
    "battery_jumpstart",
    "tire_change",
    "engine_repair",
]


VEHICLE_TYPE_NAMES = [
    "motorcycle",
    "scooter",
    "moped",
    "auto_rickshaw",
    "e_rickshaw",
    "car",
    "taxi",
    "suv",
    "van",
    "ambulance",
    "bus",
    "truck",
    "mini_truck",
    "light_truck",
    "heavy_truck",
    "tractor",
    "tractor_trailer",
    "construction_vehicle",
    "pickup_truck",
]


# Real Bengaluru roadside-assistance/mechanic businesses.
#
# Coordinates and ratings are from the provider data we researched.
# vehicle_types and capabilities are assigned conservatively based
# on the services these businesses advertise/list.
#
# is_available is application/demo state, NOT claimed live availability.

REAL_PROVIDERS = [
    {
        "name": "RESCUE Roadside Assistance",
        "lat": 12.9676733,
        "lng": 77.6112868,
        "vehicle_types": [
            "motorcycle",
            "scooter",
            "car",
            "suv",
        ],
        "rating": 4.7,
        "caps": [
            "towing",
            "battery_jumpstart",
            "tire_change",
        ],
    },
    {
        "name": "Star Car Towing Service Bangalore",
        "lat": 12.9916401,
        "lng": 77.6000889,
        "vehicle_types": [
            "car",
            "suv",
            "truck",
        ],
        "rating": 5.0,
        "caps": [
            "towing",
        ],
    },
    {
        "name": "On Time Assist Towing Service",
        "lat": 12.9574859,
        "lng": 77.7028867,
        "vehicle_types": [
            "car",
            "suv",
        ],
        "rating": 5.0,
        "caps": [
            "towing",
        ],
    },
    {
        "name": "Shivaraj Towing Service",
        "lat": 13.0406486,
        "lng": 77.5155149,
        "vehicle_types": [
            "car",
            "suv",
            "truck",
        ],
        "rating": 5.0,
        "caps": [
            "towing",
        ],
    },
    {
        "name": "Express Car Service",
        "lat": 12.9388221,
        "lng": 77.5299434,
        "vehicle_types": [
            "car",
            "suv",
        ],
        "rating": 4.8,
        "caps": [
            "engine_repair",
        ],
    },
    {
        "name": "Gundappa Car Care",
        "lat": 12.9282070,
        "lng": 77.6081494,
        "vehicle_types": [
            "car",
        ],
        "rating": 5.0,
        "caps": [
            "engine_repair",
        ],
    },
    {
        "name": "GoMechanic - Bangalore (HQ)",
        "lat": 12.9375954,
        "lng": 77.6269476,
        "vehicle_types": [
            "car",
            "suv",
        ],
        "rating": 4.2,
        "caps": [
            "engine_repair",
            "battery_jumpstart",
        ],
    },
    {
        "name": "R.K. Puncture Shop 24/7",
        "lat": 13.0173672,
        "lng": 77.6703413,
        "vehicle_types": [
            "motorcycle",
            "scooter",
            "car",
        ],
        "rating": 3.6,
        "caps": [
            "tire_change",
        ],
    },
    {
        "name": "AYS Tyre Puncture Shop Koramangala",
        "lat": 12.9338433,
        "lng": 77.6195370,
        "vehicle_types": [
            "motorcycle",
            "scooter",
            "car",
        ],
        "rating": 4.7,
        "caps": [
            "tire_change",
        ],
    },
    {
        "name": "Puncture Shop Bharath Tyres",
        "lat": 12.9001575,
        "lng": 77.6225438,
        "vehicle_types": [
            "motorcycle",
            "scooter",
            "car",
            "suv",
        ],
        "rating": 4.7,
        "caps": [
            "tire_change",
        ],
    },
    {
        "name": "Roadside Assistance M.A Car Jumpstart Service",
        "lat": 13.0205457,
        "lng": 77.6000786,
        "vehicle_types": [
            "car",
        ],
        "rating": 5.0,
        "caps": [
            "battery_jumpstart",
        ],
    },
    {
        "name": "RAPID Roadside Assistance 24/7",
        "lat": 13.0417759,
        "lng": 77.5937925,
        "vehicle_types": [
            "motorcycle",
            "scooter",
            "car",
            "suv",
        ],
        "rating": 4.9,
        "caps": [
            "battery_jumpstart",
        ],
    },
]


def seed():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # ---------------------------------------------
        # Create capabilities
        # ---------------------------------------------

        cap_lookup = {}

        for name in CAPABILITY_NAMES:
            cap = (
                db.query(Capability)
                .filter_by(name=name)
                .first()
            )

            if not cap:
                cap = Capability(name=name)
                db.add(cap)
                db.flush()

            cap_lookup[name] = cap

        # ---------------------------------------------
        # Create vehicle types
        # ---------------------------------------------

        vehicle_lookup = {}

        for name in VEHICLE_TYPE_NAMES:
            vehicle_type = (
                db.query(VehicleType)
                .filter_by(name=name)
                .first()
            )

            if not vehicle_type:
                vehicle_type = VehicleType(name=name)
                db.add(vehicle_type)
                db.flush()

            vehicle_lookup[name] = vehicle_type

        # ---------------------------------------------
        # Create providers
        # ---------------------------------------------

        for p in REAL_PROVIDERS:
            exists = (
                db.query(Provider)
                .filter_by(name=p["name"])
                .first()
            )

            if exists:
                continue

            provider = Provider(
                name=p["name"],
                latitude=p["lat"],
                longitude=p["lng"],
                rating=p["rating"],
                is_available=True,
            )

            # Provider capabilities
            provider.capabilities = [
                cap_lookup[c]
                for c in p["caps"]
            ]

            # Provider-supported vehicle types
            provider.vehicle_types = [
                vehicle_lookup[v]
                for v in p["vehicle_types"]
            ]

            db.add(provider)

        db.commit()

        print("Seed complete.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()