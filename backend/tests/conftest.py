import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import Base, get_db
from app.db.models import Provider, Capability, VehicleType
from app.main import app

TEST_DB_URL = "sqlite:///./test.db"


@pytest.fixture(scope="function")
def test_db():
    """
    Fresh, isolated SQLite DB per test function.
    Never touches breakdown_assist.db (the real dev database).
    """
    if os.path.exists("./test.db"):
        os.remove("./test.db")

    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()
        if os.path.exists("./test.db"):
            os.remove("./test.db")


@pytest.fixture(scope="function")
def client(test_db):
    """FastAPI TestClient wired to the isolated test DB via dependency override."""

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def seed_two_towing_providers(test_db):
    """
    Minimal, controlled provider set for match/replan tests.
    Deliberately NOT the real dev seed data -- fixed, predictable coordinates
    so distance/ranking assertions are deterministic.
    """
    towing = Capability(name="towing")
    car_type = VehicleType(name="car")
    test_db.add_all([towing, car_type])
    test_db.flush()

    near_provider = Provider(
        name="Near Towing Co",
        latitude=12.9716,
        longitude=77.5946,
        rating=4.5,
        is_available=True,
    )
    near_provider.capabilities = [towing]
    near_provider.vehicle_types = [car_type]

    far_provider = Provider(
        name="Far Towing Co",
        latitude=13.2000,
        longitude=77.8000,
        rating=4.5,
        is_available=True,
    )
    far_provider.capabilities = [towing]
    far_provider.vehicle_types = [car_type]

    test_db.add_all([near_provider, far_provider])
    test_db.commit()

    return {"near": near_provider, "far": far_provider}