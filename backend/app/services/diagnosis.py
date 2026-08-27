FAULT_TO_CAPABILITY = {
    "Rich Mixture": "engine_repair",
    "Lean Mixture": "engine_repair",
    "Low Voltage": "battery_jumpstart",
}


def get_required_capability(fault_name: str) -> str | None:
    return FAULT_TO_CAPABILITY.get(fault_name)