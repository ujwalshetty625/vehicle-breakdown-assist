"""
Unit tests for app/services/matching.py pure functions.
No DB, no server -- fast, isolated math checks.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.matching import haversine_km, score_provider, RATING_WEIGHT


def test_haversine_zero_distance_same_point():
    """Distance between a point and itself must be 0."""
    d = haversine_km(12.9716, 77.5946, 12.9716, 77.5946)
    assert d == 0.0


def test_haversine_known_distance():
    """
    Bengaluru (12.9716, 77.5946) to Chennai (13.0827, 80.2707) is
    a well-known real-world distance of approximately 290 km.
    Allow generous tolerance since Haversine is straight-line, not road distance.
    """
    d = haversine_km(12.9716, 77.5946, 13.0827, 80.2707)
    assert 280 <= d <= 300


def test_score_provider_formula():
    """score = distance_km - (rating * RATING_WEIGHT). Verify exact formula, not just behavior."""
    score = score_provider(distance_km=10.0, rating=5.0)
    expected = 10.0 - (5.0 * RATING_WEIGHT)
    assert score == expected


def test_score_provider_lower_is_better():
    """A closer OR higher-rated provider should score lower (better)."""
    close_low_rated = score_provider(distance_km=2.0, rating=3.0)
    far_high_rated = score_provider(distance_km=15.0, rating=5.0)
    same_distance_higher_rating = score_provider(distance_km=10.0, rating=5.0)
    same_distance_lower_rating = score_provider(distance_km=10.0, rating=3.0)

    # Higher rating at same distance must produce a lower (better) score
    assert same_distance_higher_rating < same_distance_lower_rating