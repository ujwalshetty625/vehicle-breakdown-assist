from datetime import datetime


# --- Documented design assumptions (not measured/real-time data) ---
NIGHT_START_HOUR = 21  # 9 PM
NIGHT_END_HOUR = 6     # 6 AM

# Distance -> rough ETA band. These are stated assumptions for a rough estimate,
# not live traffic/routing data. Roughly ~20-24 km/h average, accounting for city traffic.
DISTANCE_BANDS = [
    (5, "5-15 min", "nearby"),
    (8, "15-25 min", "some_wait"),
    (12, "20-35 min", "far"),
    (20, "30-50 min", "very_far"),
    (float("inf"), "50+ min", "very_long_wait"),
]

SEVERITY_RANK = {
    "none": 0,
    "medium": 1,
    "high": 2,
    "unknown": 1,  # unknown treated as medium
}


def is_night(current_time: datetime | None = None) -> bool:
    """Night defined as 9 PM - 6 AM, server local time.
    Documented design choice, not a measured risk signal.
    """
    t = current_time or datetime.now()
    hour = t.hour
    return hour >= NIGHT_START_HOUR or hour < NIGHT_END_HOUR


def get_distance_band(distance_km: float) -> tuple[str, str]:
    """Returns (eta_range_label, interpretation) for a given distance,
    per documented bands.
    """
    for max_km, eta_label, interpretation in DISTANCE_BANDS:
        if distance_km <= max_km:
            return eta_label, interpretation

    return DISTANCE_BANDS[-1][1], DISTANCE_BANDS[-1][2]


def assess_roadside_safety(
    severity: str,
    safe_to_drive: bool | None,
    distance_km: float | None,
    matched: bool,
    assistance_required: bool = True,
    current_time: datetime | None = None,
) -> dict:
    """
    Produces waiting/roadside guidance from objective, available factors only:
    severity, time of day, distance-based rough ETA band, and match status.

    assistance_required explicitly distinguishes between:
    - a case where no roadside assistance is needed at all, and
    - a case where assistance is needed but no provider is currently matched.

    Deliberately does NOT infer or use occupant demographics, or claim real-time
    location-safety intelligence we don't have.
    """
    night = is_night(current_time)
    severity_level = SEVERITY_RANK.get(severity, 1)

    eta_label, distance_interpretation = (
        get_distance_band(distance_km) if distance_km is not None else (None, None)
    )

    long_wait = distance_interpretation in (
        "far",
        "very_far",
        "very_long_wait",
    )

    context_note = (
        "Recommendation is based on fault severity, time of day, and a rough "
        "distance-based ETA band. ETA is an estimate, not live traffic/routing "
        "data. Real-time location-safety data is not integrated."
    )

    # --- No assistance was ever needed: not an escalation, nothing to wait for ---
    if not assistance_required:
        return {
            "risk_level": "none",
            "guidance": (
                "No fault detected requiring roadside assistance. "
                "No special waiting guidance needed."
            ),
            "eta_estimate": None,
            "distance_interpretation": None,
            "is_night": night,
            "context_note": context_note,
        }

    # --- No provider matched at all: highest-priority escalation ---
    if not matched:
        return {
            "risk_level": "elevated",
            "guidance": (
                "No provider is currently available. Consider re-attempting "
                "matching shortly, and if the situation feels unsafe, prioritize "
                "contacting local emergency services."
            ),
            "eta_estimate": None,
            "distance_interpretation": None,
            "is_night": night,
            "context_note": context_note,
        }

    # --- Cannot safely drive: always prioritize assistance regardless of time ---
    if safe_to_drive is False:
        base_guidance = (
            "Do not continue driving. Prioritize waiting safely for assistance."
        )

        if night and long_wait:
            guidance = (
                base_guidance
                + " Given the extended wait and nighttime conditions, consider "
                "moving to a well-lit, public location near your breakdown point "
                "if one is safely reachable, and keep hazard lights on."
            )
            risk_level = "high"

        elif night or long_wait:
            guidance = (
                base_guidance
                + " Keep hazard lights on and remain visible while waiting."
            )
            risk_level = "elevated"

        else:
            guidance = base_guidance
            risk_level = "moderate"

        return {
            "risk_level": risk_level,
            "guidance": guidance,
            "eta_estimate": eta_label,
            "distance_interpretation": distance_interpretation,
            "is_night": night,
            "context_note": context_note,
        }

    # --- Safe to drive, but still assess severity/time/wait combination ---
    if night and severity_level >= 2:
        guidance = (
            "Vehicle can be driven, but given the fault severity and nighttime "
            "conditions, consider heading directly to the assigned provider or "
            "a well-lit public area rather than waiting roadside."
        )
        risk_level = "elevated"

    elif night and long_wait:
        guidance = (
            "Consider waiting in a well-lit, visible area while assistance arrives."
        )
        risk_level = "moderate"

    else:
        guidance = (
            "Normal waiting guidance: remain with your vehicle in a safe location "
            "until assistance arrives."
        )
        risk_level = "low"

    return {
        "risk_level": risk_level,
        "guidance": guidance,
        "eta_estimate": eta_label,
        "distance_interpretation": distance_interpretation,
        "is_night": night,
        "context_note": context_note,
    }