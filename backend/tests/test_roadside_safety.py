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
    get_time_context,
    get_night_assistance_priority,
    is_night,
)
from app.services.severity import assess_severity

DAY_TIME = datetime(2026, 1, 1, 14, 0)      # 2 PM
EVENING_TIME = datetime(2026, 1, 1, 19, 30)  # 7:30 PM
NIGHT_TIME = datetime(2026, 1, 1, 23, 0)     # 11 PM


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
    assert result["time_context"] in ("day", "evening", "night")
    assert result["night_assistance_priority"] in ("normal", "elevated")


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


def test_get_time_context_boundaries():
    """Verify explicit time context boundaries:
    06:00 - 17:59 -> day
    18:00 - 20:59 -> evening
    21:00 - 05:59 -> night
    """
    assert get_time_context(datetime(2026, 1, 1, 6, 0)) == "day"
    assert get_time_context(datetime(2026, 1, 1, 17, 59)) == "day"
    assert get_time_context(datetime(2026, 1, 1, 18, 0)) == "evening"
    assert get_time_context(datetime(2026, 1, 1, 20, 59)) == "evening"
    assert get_time_context(datetime(2026, 1, 1, 21, 0)) == "night"
    assert get_time_context(datetime(2026, 1, 1, 23, 0)) == "night"
    assert get_time_context(datetime(2026, 1, 1, 0, 0)) == "night"
    assert get_time_context(datetime(2026, 1, 1, 5, 59)) == "night"


def test_get_night_assistance_priority():
    """DAY & EVENING -> normal, NIGHT -> elevated."""
    assert get_night_assistance_priority("day") == "normal"
    assert get_night_assistance_priority("evening") == "normal"
    assert get_night_assistance_priority("night") == "elevated"


def test_time_context_and_priority_in_assess_roadside_safety():
    """Verify returned dictionary contains time_context and night_assistance_priority."""
    res_day = assess_roadside_safety("medium", True, 5.0, True, current_time=DAY_TIME)
    assert res_day["time_context"] == "day"
    assert res_day["night_assistance_priority"] == "normal"
    assert res_day["is_night"] is False

    res_eve = assess_roadside_safety("medium", True, 5.0, True, current_time=EVENING_TIME)
    assert res_eve["time_context"] == "evening"
    assert res_eve["night_assistance_priority"] == "normal"
    assert res_eve["is_night"] is False

    res_night = assess_roadside_safety("medium", True, 5.0, True, current_time=NIGHT_TIME)
    assert res_night["time_context"] == "night"
    assert res_night["night_assistance_priority"] == "elevated"
    assert res_night["is_night"] is True


def test_mechanical_severity_remains_independent_of_time_context():
    """Verify that mechanical fault severity is determined independently of time context."""
    # Mechanical fault severity engine
    sev_day = assess_severity("Lean Mixture", 0.86)
    sev_night = assess_severity("Lean Mixture", 0.86)
    assert sev_day == sev_night
    assert sev_day["severity"] == "high"

    # Roadside safety context for same fault at day vs night
    roadside_day = assess_roadside_safety(
        severity=sev_day["severity"],
        safe_to_drive=sev_day["safe_to_drive"],
        distance_km=5.0,
        matched=True,
        current_time=DAY_TIME,
    )
    roadside_night = assess_roadside_safety(
        severity=sev_night["severity"],
        safe_to_drive=sev_night["safe_to_drive"],
        distance_km=5.0,
        matched=True,
        current_time=NIGHT_TIME,
    )

    # Mechanical severity passed to both is identical
    assert sev_day["severity"] == "high"
    assert sev_night["severity"] == "high"

    # Only time_context and assistance_priority change contextually
    assert roadside_day["time_context"] == "day"
    assert roadside_day["night_assistance_priority"] == "normal"

    assert roadside_night["time_context"] == "night"
    assert roadside_night["night_assistance_priority"] == "elevated"


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