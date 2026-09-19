# REST API Documentation: Vehicle Breakdown Assist

Base URL: `http://localhost:8000` (or configured deployment host)  
Content-Type: `application/json`

---

## 1. Summary of Endpoints

| Method | Endpoint | Description | Primary Subsystem |
|---|---|---|---|
| `GET` | `/` | API root health and status check | Core |
| `GET` | `/health` | Service health probe | Core |
| `POST` | `/assist` | Unified multimodal breakdown diagnosis, safety analysis, and provider dispatch | AI / Matching / Safety |
| `POST` | `/diagnose` | Standalone 14-parameter OBD-II telemetry ML fault diagnosis | ML Diagnostics |
| `GET` | `/diagnostics/presets` | Retrieve all predefined OBD-II vehicle diagnostic telemetry profiles | Telemetry Simulation |
| `GET` | `/diagnostics/presets/{id}` | Retrieve a specific OBD-II diagnostic preset by ID | Telemetry Simulation |
| `POST` | `/diagnostics/scan` | Simulate automated vehicle ECU / OBD-II telemetry scan | Telemetry Simulation |
| `GET` | `/providers` | List all registered service providers and their capabilities | Provider Directory |
| `POST` | `/providers` | Register a new roadside service provider | Provider Management |
| `POST` | `/match-provider` | Direct capability & location provider matching without full telemetry | Geospatial Matching |
| `POST` | `/replan` | Reallocate assignment to next best provider excluding failed provider | Adaptive Recovery |
| `GET` | `/vehicle-types` | List all supported vehicle categories and taxonomy mappings | Vehicle Master Data |

---

## 2. Detailed Endpoint Specifications

### 2.1 Unified Multimodal Assistance (`POST /assist`)

Primary entry point for the frontend breakdown submission. Combines 14 OBD-II sensor values, dashboard image base64 data, user symptoms, location, and vehicle type.

#### Request Headers
```http
Content-Type: application/json
```

#### Request Body Schema (`AssistRequest`)
```json
{
  "vehicle_type": "car",
  "latitude": 12.9345,
  "longitude": 77.6265,
  "symptoms": "Heavy black smoke from exhaust and severe power loss",
  "warning_light": "Check Engine",
  "engine_photo": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "MAP": 1.044,
  "TPS": 0.769,
  "Force": 80.04,
  "Power": 0.497,
  "RPM": 1188.55,
  "consumption_lh": 1.989,
  "consumption_l100km": 8.207,
  "Speed": 25.038,
  "CO": 1.925,
  "HC": 247.44,
  "CO2": 12.834,
  "O2": 0.56,
  "Lambda": 1.003,
  "AFR": 14.75
}
```

#### Response Body (`200 OK`)
```json
{
  "diagnosis": {
    "fault_type": 1,
    "fault_name": "Rich Mixture",
    "confidence": 0.88,
    "class_probabilities": [0.03, 0.88, 0.05, 0.04]
  },
  "cv_analysis": {
    "warning_light": "check_engine",
    "label": "Check Engine / Malfunction Indicator",
    "confidence": 0.9412,
    "recommended_capability": "engine_repair",
    "severity": "medium",
    "safe_to_drive": false,
    "recommended_action": "Check engine light illuminated. Have vehicle inspected to prevent catalytic converter damage."
  },
  "severity": {
    "severity": "high",
    "safe_to_drive": false,
    "low_confidence": false,
    "advisory": "High combustion fuel ratio detected. Continued driving may cause catalytic converter failure. Turn off engine and await assistance."
  },
  "roadside_safety": {
    "risk_level": "moderate",
    "guidance": "Do not continue driving. Keep hazard lights on and remain visible while waiting.",
    "eta_estimate": "5-15 min",
    "distance_interpretation": "nearby",
    "is_night": false,
    "time_context": "day",
    "night_assistance_priority": "normal",
    "context_note": "Recommendation is based on fault severity, time of day, and a rough distance-based ETA band."
  },
  "assistance_required": true,
  "required_capability": "engine_repair",
  "matched": true,
  "message": "Matched with Apex Auto Diagnostics & Repair.",
  "assignment_id": 42,
  "assigned_provider": {
    "id": 3,
    "name": "Apex Auto Diagnostics & Repair",
    "phone": "+91 98450 11223",
    "email": "dispatch@apexautofix.com",
    "distance_km": 2.45,
    "rating": 4.8,
    "score": -7.15,
    "latitude": 12.9412,
    "longitude": 77.6189,
    "capabilities": ["engine_repair", "battery_jumpstart", "towing"],
    "vehicle_types": ["car", "suv", "van"]
  },
  "ranked_candidates": [
    {
      "id": 3,
      "name": "Apex Auto Diagnostics & Repair",
      "distance_km": 2.45,
      "rating": 4.8,
      "score": -7.15
    },
    {
      "id": 7,
      "name": "Koramangala 24/7 Roadside Rescue",
      "distance_km": 4.12,
      "rating": 4.5,
      "score": -4.88
    }
  ]
}
```

---

### 2.2 Telemetry Fault Diagnosis (`POST /diagnose`)

Direct inference endpoint for the 14-parameter Random Forest model.

#### Request Body
```json
{
  "MAP": 1.685,
  "TPS": 0.983,
  "Force": 283.63,
  "Power": 3.236,
  "RPM": 1878.75,
  "consumption_lh": 3.202,
  "consumption_l100km": 7.952,
  "Speed": 40.384,
  "CO": 0.462,
  "HC": 214.24,
  "CO2": 12.971,
  "O2": 0.87,
  "Lambda": 1.04,
  "AFR": 15.284
}
```

#### Response Body
```json
{
  "fault_type": 3,
  "fault_name": "Low Voltage",
  "confidence": 0.9124,
  "class_probabilities": [0.0215, 0.0341, 0.032, 0.9124]
}
```

---

### 2.3 Adaptive Re-planning (`POST /replan`)

Triggered when an assigned recovery provider fails to arrive, rejects the dispatch, or cancels.

#### Request Body
```json
{
  "assignment_id": 42,
  "exclude_provider_id": 3
}
```

#### Response Body
```json
{
  "status": "reassigned",
  "message": "Assignment #42 reassigned from provider #3 to Koramangala 24/7 Roadside Rescue.",
  "assignment_id": 42,
  "previous_provider_id": 3,
  "assigned_provider": {
    "id": 7,
    "name": "Koramangala 24/7 Roadside Rescue",
    "phone": "+91 99800 44556",
    "email": "help@koramangalarescue.in",
    "distance_km": 4.12,
    "rating": 4.5,
    "score": -4.88,
    "latitude": 12.951,
    "longitude": 77.632,
    "capabilities": ["towing", "engine_repair", "battery_jumpstart", "tire_change"],
    "vehicle_types": ["car", "motorcycle", "suv", "auto_rickshaw"]
  },
  "remaining_candidates": 3
}
```

---

### 2.4 Diagnostic Presets & ECU Auto-Scan (`GET /diagnostics/presets`, `POST /diagnostics/scan`)

Allows frontend users to test real benchmark telemetry profiles from EngineFaultDB or simulate an OBD-II dongle scan.

#### `POST /diagnostics/scan` Request Body
```json
{
  "vehicle_model": "Hyundai Creta",
  "vehicle_type": "car",
  "symptoms": "Clicking sound and dead battery in morning"
}
```

#### `POST /diagnostics/scan` Response Body
```json
{
  "status": "success",
  "message": "ECU Diagnostic Scan successful for Hyundai Creta",
  "matched_preset": "Battery Dead & Low Alternator Voltage",
  "fault_hypothesis": "Low Voltage",
  "telemetry": {
    "MAP": 1.685,
    "TPS": 0.983,
    "Force": 283.63,
    "Power": 3.236,
    "RPM": 1878.75,
    "consumption_lh": 3.202,
    "consumption_l100km": 7.952,
    "Speed": 40.384,
    "CO": 0.462,
    "HC": 214.24,
    "CO2": 12.971,
    "O2": 0.87,
    "Lambda": 1.04,
    "AFR": 15.284
  }
}
```

---

### 2.5 Provider Directory (`GET /providers`)

Returns all seeded service stations, mechanics, and towing operators.

#### Response Body
```json
[
  {
    "id": 1,
    "name": "City Tow & Recovery Services",
    "phone": "+91 98450 12345",
    "email": "dispatch@citytow.in",
    "latitude": 12.9352,
    "longitude": 77.6245,
    "rating": 4.7,
    "is_available": true,
    "capabilities": ["towing", "tire_change"],
    "vehicle_types": ["car", "suv", "truck", "van"]
  }
]
```

---

### 2.6 Vehicle Taxonomy & Types (`GET /vehicle-types`)

Returns all supported vehicle categories with canonical identifiers and metadata.

#### Response Body
```json
[
  { "id": "car", "name": "Four-Wheeler / Car", "category": "Light Motor Vehicle" },
  { "id": "motorcycle", "name": "Two-Wheeler / Bike / Scooter", "category": "Two Wheeler" },
  { "id": "suv", "name": "SUV / Compact 4x4", "category": "Utility Vehicle" },
  { "id": "auto_rickshaw", "name": "Auto Rickshaw / 3-Wheeler", "category": "Commercial 3-Wheeler" },
  { "id": "truck", "name": "Commercial Truck / Lorry", "category": "Heavy Commercial" },
  { "id": "van", "name": "Van / Minivan / Commercial Carrier", "category": "Light Commercial" }
]
```
