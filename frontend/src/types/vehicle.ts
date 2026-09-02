export type VehicleType =
    | "motorcycle"
    | "scooter"
    | "moped"
    | "auto_rickshaw"
    | "e_rickshaw"
    | "car"
    | "taxi"
    | "suv"
    | "van"
    | "ambulance"
    | "bus"
    | "truck"
    | "mini_truck"
    | "light_truck"
    | "heavy_truck"
    | "tractor"
    | "tractor_trailer"
    | "construction_vehicle"
    | "pickup_truck"
    | (string & {});


export interface VehicleTypeOption {
    id: string;
    name: string;
    icon: string;
    category: string;
    in_db?: boolean;
}


export interface VehicleCategoryGroup {
    category: string;
    vehicles: VehicleTypeOption[];
}


export interface TelemetryData {
    MAP: number;
    TPS: number;
    Force: number;
    Power: number;
    RPM: number;
    consumption_lh: number;
    consumption_l100km: number;
    Speed: number;
    CO: number;
    HC: number;
    CO2: number;
    O2: number;
    Lambda: number;
    AFR: number;
}


export interface DiagnosticPreset {
    id: string;
    name: string;
    fault_name: string;
    description: string;
    symptoms: string;
    telemetry: TelemetryData;
}


export interface BreakdownData {
    vehicleModel: string;
    vehicleYear: string;
    vehicleType: VehicleType;
    fuelType: string;
    symptoms: string;
    warningLight: string;
    location: string;
    latitude: number | null;
    longitude: number | null;
    enginePhoto?: string;

    // ML telemetry
    MAP: number;
    TPS: number;
    Force: number;
    Power: number;
    RPM: number;
    consumption_lh: number;
    consumption_l100km: number;
    Speed: number;
    CO: number;
    HC: number;
    CO2: number;
    O2: number;
    Lambda: number;
    AFR: number;
}


export interface SeverityInfo {
    severity: "low" | "medium" | "high" | "critical" | string;
    safe_to_drive: boolean;
    low_confidence: boolean;
    advisory: string;
}


export interface RoadsideSafetyInfo {
    risk_level: "low" | "medium" | "high" | "critical" | string;
    guidance: string;
    eta_estimate: string;
    distance_interpretation: string;
    is_night: boolean;
    context_note: string;
}


export interface DiagnosisResult {
    fault: string;
    confidence: number;
    severity: string;
    safeToDrive?: boolean;
    lowConfidence?: boolean;
    advisory?: string;
    safetyRecommendation: string;
    roadsideSafety?: RoadsideSafetyInfo;
    assistanceRequired: string;
    // Optional values from the backend
    faultType?: number;
    classProbabilities?: number[];
    requiredCapability?: string | null;
}


export interface Provider {
    id: number;
    name: string;
    phone?: string | null;
    email?: string | null;
    latitude: number;
    longitude: number;
    distanceKm: number;
    etaMinutes?: number;
    rating: number;
    available: boolean;
    services: string[];
    vehicleCompatibility: string[];
    matchScore: number;
}


export interface MatchedProvider {
    id: number;
    name: string;
    phone?: string | null;
    email?: string | null;
    distance_km: number;
    rating: number;
    score: number;
    latitude?: number;
    longitude?: number;
    capabilities?: string[];
    vehicle_types?: string[];
}


export interface BackendProvider {
    id: number;
    name: string;
    phone?: string | null;
    email?: string | null;
    latitude: number;
    longitude: number;
    vehicle_types: string[];
    is_available: boolean;
    rating: number;
    capabilities: string[];
}


export interface AssistResponse {
    diagnosis: {
        fault_type: number;
        fault_name: string;
        confidence: number;
        class_probabilities: number[];
    };
    severity?: SeverityInfo;
    roadside_safety?: RoadsideSafetyInfo;
    assistance_required: boolean;
    required_capability: string | null;
    matched: boolean;
    message: string;
    assignment_id: number | null;
    assigned_provider: MatchedProvider | null;
    ranked_candidates: MatchedProvider[];
}


export interface ReplanResponse {
    matched?: boolean;
    message?: string;
    assignment_id?: number | null;
    assigned_provider?: MatchedProvider | null;
    ranked_candidates?: MatchedProvider[];
}