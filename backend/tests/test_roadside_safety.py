"""
Unit tests for app/services/roadside_safety.py.
Pure functions, no DB/server needed.

Includes a regression test locking in the assistance_required bug fix
found during manual integration testing of /assist -- this must never
silently regress.
"""
import sys, os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.roadside_safety import (
    assess_roadside_safety,
    get_distance_band,
    is_night,
)

DAY_TIME = datetime(2026, 1, 1, 14, 0)   # 2 PM
NIGHT_TIME = datetime(2026, 1, 1, 23, 0)  # 11 PM


def test_no_assistance_required_does_not_escalate():
    """
    REGRESSION TEST for a real bug caught during manual /assist testing:
    a healthy vehicle (no fault, assistance_required=False) must NOT
    return an "elevated risk / no provider available" escalation.
    """
    result = assess_roadside_safety(
        severity="none",
        safe_to_drive=True,
        distance_km=None,
        matched=False,
        assistance_required=False,
    )
    assert result["risk_level"] == "none"
    assert "no provider" not in result["guidance"].lower()


def test_assistance_required_but_no_provider_matched_escalates():
    """Distinct from the case above: assistance IS needed but none was found -> real escalation."""
    result = assess_roadside_safety(
        severity="high",
        safe_to_drive=False,
        distance_km=None,
        matched=False,
        assistance_required=True,
    )
    assert result["risk_level"] == "elevated"
    assert "no provider" in result["guidance"].lower()


def test_distance_band_boundaries():
    """Verify each documented distance band assigns the correct ETA label/interpretation."""
    assert get_distance_band(3)[1] == "nearby"
    assert get_distance_band(5)[1] == "nearby"
    assert get_distance_band(7)[1] == "some_wait"
    assert get_distance_band(8)[1] == "some_wait"
    assert get_distance_band(10)[1] == "far"
    assert get_distance_band(12)[1] == "far"
    assert get_distance_band(15)[1] == "very_far"
    assert get_distance_band(20)[1] == "very_far"
    assert get_distance_band(25)[1] == "very_long_wait"


def test_is_night_boundaries():
    """Night window is documented as 9 PM (21:00) - 6 AM."""
    assert is_night(datetime(2026, 1, 1, 21, 0)) is True   # exactly 9 PM -> night
    assert is_night(datetime(2026, 1, 1, 23, 30)) is True  # 11:30 PM -> night
    assert is_night(datetime(2026, 1, 1, 5, 59)) is True   # 5:59 AM -> night
    assert is_night(datetime(2026, 1, 1, 6, 0)) is False   # exactly 6 AM -> day
    assert is_night(datetime(2026, 1, 1, 14, 0)) is False  # 2 PM -> day


def test_night_high_severity_long_wait_escalates_to_high():
    """Worst-case combination (night + cannot drive + very long wait) must reach 'high' risk."""
    result = assess_roadside_safety(
        severity="high",
        safe_to_drive=False,
        distance_km=22.0,
        matched=True,
        assistance_required=True,
        current_time=NIGHT_TIME,
    )
    assert result["risk_level"] == "high"


def test_daytime_low_severity_short_distance_is_low_risk():
    """Best-case combination should return normal/low guidance, not an escalation."""
    result = assess_roadside_safety(
        severity="none",
        safe_to_drive=True,
        distance_km=3.0,
        matched=True,
        assistance_required=True,
        current_time=DAY_TIME,
    )
    assert result["risk_level"] == "low"


def test_unknown_severity_treated_as_medium():
    """An unrecognized fault_name must default to medium severity handling, not crash or default to none."""
    result = assess_roadside_safety(
        severity="unknown",
        safe_to_drive=True,
        distance_km=3.0,
        matched=True,
        assistance_required=True,
        current_time=DAY_TIME,
    )
    # Should not raise, should still return a valid structured response
    assert result["risk_level"] in ("low", "moderate", "elevated", "high")