FAULT_TO_CAPABILITY = {
    "Rich Mixture": "engine_repair",
    "Lean Mixture": "engine_repair",
    "Low Voltage": "battery_jumpstart",
}

FAULT_USER_FRIENDLY_NAMES = {
    "No Fault": "No issue detected",
    "Rich Mixture": "Too much fuel in the engine",
    "Lean Mixture": "Not enough fuel in the engine",
    "Low Voltage": "Battery or electrical power issue",
    "Flat Tire / Puncture Damage": "Tire or wheel issue",
    "Flat Tire": "Tire or wheel issue",
}

FAULT_DESCRIPTIONS = {
    "No Fault": "The available vehicle diagnostic data does not indicate a major fault.",
    "Rich Mixture": "The engine appears to be receiving more fuel than required, which may affect performance and fuel efficiency.",
    "Lean Mixture": "The engine appears to be receiving less fuel than required, which may lead to poor performance or uneven engine operation.",
    "Low Voltage": "The vehicle's electrical system is showing unusually low voltage, which may indicate a battery or charging-system problem.",
    "Flat Tire / Puncture Damage": "A tire has lost air pressure or suffered puncture damage, making continued driving hazardous.",
    "Flat Tire": "A tire has lost air pressure or suffered puncture damage, making continued driving hazardous.",
}


def get_required_capability(fault_name: str) -> str | None:
    return FAULT_TO_CAPABILITY.get(fault_name)


def get_user_friendly_name(fault_name: str) -> str:
    return FAULT_USER_FRIENDLY_NAMES.get(
        fault_name,
        f"Diagnostic issue detected ({fault_name})",
    )


def get_fault_description(fault_name: str) -> str:
    return FAULT_DESCRIPTIONS.get(
        fault_name,
        f"Vehicle telemetry indicates an operating anomaly ({fault_name}). An inspection is recommended to verify safe operating condition.",
    )


def get_fault_explanation(fault_name: str) -> str:
    return get_fault_description(fault_name)
