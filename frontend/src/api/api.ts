import axios from "axios";

import type {
    AssistResponse,
    BackendProvider,
    BreakdownData,
    DiagnosticPreset,
    MatchedProvider,
    Provider,
    ReplanResponse,
    VehicleCategoryGroup,
    VehicleTypeOption,
} from "../types/vehicle";


/*
 * =========================================================
 * FASTAPI BACKEND CLIENT
 * =========================================================
 */

const api = axios.create({
    baseURL: "http://127.0.0.1:8000",
    headers: {
        "Content-Type": "application/json",
    },
    timeout: 10000,
});


/*
 * =========================================================
 * HELPERS
 * =========================================================
 */

export const calculateDistanceKm = (
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number
): number => {
    if (!lat1 || !lon1 || !lat2 || !lon2) return 3.5;
    const R = 6371; // km
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLon = ((lon2 - lon1) * Math.PI) / 180;
    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos((lat1 * Math.PI) / 180) *
            Math.cos((lat2 * Math.PI) / 180) *
            Math.sin(dLon / 2) *
            Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const dist = R * c;
    return Math.max(0.35, Math.round(dist * 100) / 100);
};

const parseVehicleTypes = (
    vehicleTypes: string[] | string
): string[] => {
    if (Array.isArray(vehicleTypes)) {
        return vehicleTypes
            .map((type) => type.trim())
            .filter(Boolean);
    }

    if (typeof vehicleTypes === "string") {
        return vehicleTypes
            .split(",")
            .map((type) => type.trim())
            .filter(Boolean);
    }

    return [];
};


const mapBackendProvider = (
    provider: BackendProvider,
    match?: MatchedProvider,
    userLat: number = 12.9345,
    userLng: number = 77.6265
): Provider => {
    const dist = match?.distance_km && match.distance_km > 0
        ? match.distance_km
        : calculateDistanceKm(userLat, userLng, provider.latitude, provider.longitude);

    return {
        id: provider.id,
        name: provider.name,
        latitude: provider.latitude,
        longitude: provider.longitude,
        distanceKm: dist,
        etaMinutes: Math.max(5, Math.round(dist * 2.5)),
        rating: provider.rating ?? 4.5,
        available: provider.is_available,
        services: provider.capabilities ?? [],
        vehicleCompatibility: parseVehicleTypes(provider.vehicle_types),
        matchScore: match?.score ?? 0,
    };
};


/*
 * =========================================================
 * GET ALL PROVIDERS
 * =========================================================
 */

export const getProviders = async (userLat: number = 12.9345, userLng: number = 77.6265): Promise<Provider[]> => {
    try {
        const response = await api.get<BackendProvider[]>("/providers");
        return response.data.map((provider) => mapBackendProvider(provider, undefined, userLat, userLng));
    } catch (error) {
        console.error("GET /providers failed:", error);
        return [];
    }
};


/*
 * =========================================================
 * GET ALL VEHICLE TYPES
 * =========================================================
 */

export const getVehicleTypes = async (): Promise<{
    categories: VehicleCategoryGroup[];
    types: VehicleTypeOption[];
}> => {
    try {
        const response = await api.get<{
            categories: VehicleCategoryGroup[];
            types: VehicleTypeOption[];
        }>("/vehicle-types");
        return response.data;
    } catch (error) {
        console.error("GET /vehicle-types failed, using local fallback:", error);
        return {
            categories: [
                {
                    category: "Passenger Vehicle",
                    vehicles: [
                        { id: "car", name: "Sedan / Hatchback / Car", icon: "🚗", category: "Passenger Vehicle" },
                        { id: "suv", name: "SUV / Crossover", icon: "🚙", category: "Passenger Vehicle" },
                        { id: "pickup_truck", name: "Pickup Truck", icon: "🛻", category: "Passenger Vehicle" },
                    ]
                },
                {
                    category: "Two Wheeler",
                    vehicles: [
                        { id: "motorcycle", name: "Motorcycle / Bike", icon: "🏍️", category: "Two Wheeler" },
                        { id: "scooter", name: "Scooter / Scooty", icon: "🛵", category: "Two Wheeler" },
                        { id: "moped", name: "Moped", icon: "🛵", category: "Two Wheeler" },
                    ]
                },
                {
                    category: "Auto & Light Commercial",
                    vehicles: [
                        { id: "auto_rickshaw", name: "Auto Rickshaw", icon: "🛺", category: "Auto & Light Commercial" },
                        { id: "e_rickshaw", name: "E-Rickshaw", icon: "🛺", category: "Auto & Light Commercial" },
                        { id: "taxi", name: "Taxi / Cab", icon: "🚕", category: "Auto & Light Commercial" },
                        { id: "van", name: "Van / Minivan", icon: "🚐", category: "Auto & Light Commercial" },
                        { id: "mini_truck", name: "Mini Truck", icon: "🛻", category: "Auto & Light Commercial" },
                    ]
                },
                {
                    category: "Commercial & Heavy",
                    vehicles: [
                        { id: "bus", name: "Bus / Coach", icon: "🚌", category: "Commercial & Heavy" },
                        { id: "truck", name: "Truck", icon: "🚚", category: "Commercial & Heavy" },
                        { id: "heavy_truck", name: "Heavy Duty Truck", icon: "🚛", category: "Commercial & Heavy" },
                        { id: "tractor", name: "Tractor", icon: "🚜", category: "Commercial & Heavy" },
                        { id: "ambulance", name: "Ambulance / Emergency", icon: "🚑", category: "Commercial & Heavy" },
                    ]
                }
            ],
            types: []
        };
    }
};


/*
 * =========================================================
 * DIAGNOSTICS & TELEMETRY PRESETS
 * =========================================================
 */

export const getDiagnosticPresets = async (): Promise<DiagnosticPreset[]> => {
    try {
        const response = await api.get<DiagnosticPreset[]>("/diagnostics/presets");
        return response.data;
    } catch (error) {
        console.error("GET /diagnostics/presets failed:", error);
        return [];
    }
};


export const autoScanVehicleECU = async (
    vehicleModel: string,
    vehicleType: string,
    symptoms: string
): Promise<{
    matched_preset: string;
    fault_hypothesis: string;
    telemetry: BreakdownData["MAP"] extends number ? Record<string, number> : any;
}> => {
    try {
        const response = await api.post("/diagnostics/scan", {
            vehicle_model: vehicleModel,
            vehicle_type: vehicleType,
            symptoms: symptoms,
        });
        return response.data;
    } catch (error) {
        console.error("POST /diagnostics/scan failed:", error);
        throw error;
    }
};


/*
 * =========================================================
 * ASSIST (ML DIAGNOSIS + MATCHING)
 * =========================================================
 */

export const assist = async (
    data: BreakdownData
): Promise<AssistResponse> => {
    const payload = {
        vehicle_model: data.vehicleModel || "Vehicle",
        vehicle_year: data.vehicleYear || "2022",
        vehicle_type: data.vehicleType || "car",
        fuel_type: data.fuelType || "Petrol",
        symptoms: data.symptoms || "",
        warning_light: data.warningLight || "",
        location: data.location || "",
        latitude: data.latitude ?? 12.9345,
        longitude: data.longitude ?? 77.6265,
        engine_photo: data.enginePhoto || null,

        /* 14 ML telemetry values */
        MAP: Number(data.MAP) || 0,
        TPS: Number(data.TPS) || 0,
        Force: Number(data.Force) || 0,
        Power: Number(data.Power) || 0,
        RPM: Number(data.RPM) || 0,
        consumption_lh: Number(data.consumption_lh) || 0,
        consumption_l100km: Number(data.consumption_l100km) || 0,
        Speed: Number(data.Speed) || 0,
        CO: Number(data.CO) || 0,
        HC: Number(data.HC) || 0,
        CO2: Number(data.CO2) || 0,
        O2: Number(data.O2) || 0,
        Lambda: Number(data.Lambda) || 0,
        AFR: Number(data.AFR) || 0,
    };

    console.log("========== POST /assist ==========", payload);

    try {
        const response = await api.post<AssistResponse>("/assist", payload);
        console.log("Assist response:", response.data);
        return response.data;
    } catch (error) {
        console.error("POST /assist failed:", error);
        throw error;
    }
};


/*
 * =========================================================
 * REPLAN ASSISTANCE
 * =========================================================
 */

export const replanAssistance = async (
    assignmentId: number
): Promise<ReplanResponse> => {
    try {
        const response = await api.post<ReplanResponse>("/replan", {
            assignment_id: assignmentId,
        });
        return response.data;
    } catch (error) {
        console.error("POST /replan failed:", error);
        throw error;
    }
};


export default api;