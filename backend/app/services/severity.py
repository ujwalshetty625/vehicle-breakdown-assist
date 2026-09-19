SEVERITY_MAP = {
    "No Fault": {"severity": "none", "safe_to_drive": True},
    "Rich Mixture": {"severity": "medium", "safe_to_drive": True},
    "Lean Mixture": {"severity": "high", "safe_to_drive": False},  # can damage engine if driven
    "Low Voltage": {"severity": "high", "safe_to_drive": False},   # risk of stalling/no restart
    "Flat Tire / Puncture Damage": {"severity": "medium", "safe_to_drive": False},
    "Flat Tire": {"severity": "medium", "safe_to_drive": False},
}

LOW_CONFIDENCE_THRESHOLD = 0.55  # below this, model is likely guessing (see model_card.md F1 scores)


def assess_severity(fault_name: str, confidence: float) -> dict:
    base = SEVERITY_MAP.get(fault_name, {"severity": "unknown", "safe_to_drive": None})
    is_low_confidence = confidence < LOW_CONFIDENCE_THRESHOLD

    advisory = _build_advisory(fault_name, base["severity"], is_low_confidence)

    return {
        "severity": base["severity"],
        "safe_to_drive": base["safe_to_drive"],
        "low_confidence": is_low_confidence,
        "advisory": advisory,
    }


def _build_advisory(fault_name: str, severity: str, low_confidence: bool) -> str:
    if fault_name == "No Fault":
        return "No fault detected. No immediate action needed."

    msg = f"Detected: {fault_name} (severity: {severity})."
    if low_confidence:
        msg += " Model confidence is low for this fault class — treat this as a preliminary indication, not a certain diagnosis."
    if severity == "high":
        msg += " Recommend not continuing to drive until inspected."
    return msg