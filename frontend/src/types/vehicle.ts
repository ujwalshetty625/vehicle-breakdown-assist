export interface BreakdownData {
    vehicleModel: string;
    vehicleYear: string;
    fuelType: string;
    symptoms: string;
    warningLight: string;
    location: string;
    latitude?: number | null;
    longitude?: number | null;
}

export interface DiagnosisResult {
    fault: string;
    confidence: number;
    severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
    safetyRecommendation: string;
    assistanceRequired: string;
}

export interface Provider {
    id: number;
    name: string;
    latitude: number;
    longitude: number;
    distanceKm: number;
    etaMinutes: number;
    rating: number;
    available: boolean;
    services: string[];
    vehicleCompatibility: string[];
    matchScore: number;
}