"""
Integration tests for POST /match-provider and POST /replan.
Uses an isolated in-memory-style test DB (see conftest.py) -- never touches
the real development database or its provider availability state.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_match_provider_success(client, seed_two_towing_providers):
    response = client.post(
        "/match-provider",
        json={
            "required_capability": "towing",
            "vehicle_type": "car",
            "latitude": 12.9716,
            "longitude": 77.5946,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["matched"] is True
    assert data["assigned_provider"]["name"] == "Near Towing Co"
    assert data["assignment_id"] is not None
    assert data["assigned_provider"]["distance_km"] < 1.0


def test_match_provider_no_match_for_unsupported_capability(client, seed_two_towing_providers):
    response = client.post(
        "/match-provider",
        json={
            "required_capability": "engine_repair",
            "vehicle_type": "car",
            "latitude": 12.9716,
            "longitude": 77.5946,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["matched"] is False
    assert data["assigned_provider"] is None
    assert data["ranked_candidates"] == []


def test_match_provider_marks_provider_unavailable(client, seed_two_towing_providers, test_db):
    from app.db.models import Provider

    client.post(
        "/match-provider",
        json={
            "required_capability": "towing",
            "vehicle_type": "car",
            "latitude": 12.9716,
            "longitude": 77.5946,
        },
    )
    near = test_db.query(Provider).filter_by(name="Near Towing Co").first()
    assert near.is_available is False


def test_replan_frees_old_provider_and_assigns_alternative(client, seed_two_towing_providers, test_db):
    from app.db.models import Provider, Assignment

    match_response = client.post(
        "/match-provider",
        json={
            "required_capability": "towing",
            "vehicle_type": "car",
            "latitude": 12.9716,
            "longitude": 77.5946,
        },
    )
    assignment_id = match_response.json()["assignment_id"]

    replan_response = client.post("/replan", json={"assignment_id": assignment_id})
    assert replan_response.status_code == 200
    replan_data = replan_response.json()

    assert replan_data["matched"] is True
    assert replan_data["assigned_provider"]["name"] == "Far Towing Co"

    near = test_db.query(Provider).filter_by(name="Near Towing Co").first()
    assert near.is_available is True

    old_assignment = test_db.query(Assignment).filter_by(id=assignment_id).first()
    assert old_assignment.status == "failed"


def test_replan_on_already_failed_assignment_returns_400(client, seed_two_towing_providers):
    match_response = client.post(
        "/match-provider",
        json={
            "required_capability": "towing",
            "vehicle_type": "car",
            "latitude": 12.9716,
            "longitude": 77.5946,
        },
    )
    assignment_id = match_response.json()["assignment_id"]

    client.post("/replan", json={"assignment_id": assignment_id})

    second_replan = client.post("/replan", json={"assignment_id": assignment_id})
    assert second_replan.status_code == 400


def test_replan_on_nonexistent_assignment_returns_404(client, seed_two_towing_providers):
    response = client.post("/replan", json={"assignment_id": 9999})
    assert response.status_code == 404


def test_replan_exhausts_all_providers_returns_no_match(client, seed_two_towing_providers, test_db):
    """
    With only 2 providers total, after one match + one replan, both providers
    have been used. Directly mark both unavailable to simulate true exhaustion
    (replan legitimately frees a rejected provider for OTHER breakdowns, so a
    second replan alone doesn't naturally exhaust a 2-provider pool -- this
    test forces the exhaustion scenario explicitly).
    """
    from app.db.models import Provider

    match_response = client.post(
        "/match-provider",
        json={
            "required_capability": "towing",
            "vehicle_type": "car",
            "latitude": 12.9716,
            "longitude": 77.5946,
        },
    )
    assignment_id = match_response.json()["assignment_id"]

    replan_response = client.post("/replan", json={"assignment_id": assignment_id})
    second_assignment_id = replan_response.json()["assignment_id"]

    test_db.query(Provider).update({"is_available": False})
    test_db.commit()

    final_replan = client.post("/replan", json={"assignment_id": second_assignment_id})
    assert final_replan.status_code == 200
    assert final_replan.json()["matched"] is False