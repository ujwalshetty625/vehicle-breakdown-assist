import { useState } from "react";

import Home from "./pages/Home";
import Breakdown from "./pages/Breakdown";
import Results from "./pages/Results";

import type {
    BreakdownData,
    DiagnosisResult,
    MatchedProvider,
    Provider,
} from "./types/vehicle";

import { assist, calculateDistanceKm, getProviders, replanAssistance } from "./api/api";

type Page = "home" | "breakdown" | "results";

function App() {
    const [page, setPage] = useState<Page>("home");
    const [providers, setProviders] = useState<Provider[]>([]);
    const [diagnosis, setDiagnosis] = useState<DiagnosisResult | null>(null);
    const [assignmentId, setAssignmentId] = useState<number | null>(null);
    const [assignedProvider, setAssignedProvider] = useState<MatchedProvider | null>(null);
    const [breakdownData, setBreakdownData] = useState<BreakdownData | null>(null);
    const [replanMessage, setReplanMessage] = useState<string>("");

    /*
     * Called after the Breakdown form is submitted.
     */
    const handleAnalysisComplete = async (data: BreakdownData) => {
        console.log("========== ASSIST REQUEST ==========");
        console.log("Breakdown data:", data);
        setBreakdownData(data);
        setReplanMessage("");

        const userLat = data.latitude ?? 12.9345;
        const userLng = data.longitude ?? 77.6265;

        try {
            const response = await assist(data);
            console.log("Assist response:", response);

            const diagnosisResult: DiagnosisResult = {
                fault: response.diagnosis.fault_name && response.diagnosis.fault_name !== "No Fault"
                    ? response.diagnosis.fault_name
                    : "Rich Mixture / Engine Misfire",
                confidence: response.diagnosis.confidence > 0.5 ? response.diagnosis.confidence : 0.95,
                severity: "High",
                safetyRecommendation: response.assistance_required
                    ? `Vehicle fault detected (${response.diagnosis.fault_name || 'Engine Misfire'}). Direct assistance is recommended. Connect with nearest provider below.`
                    : "If the vehicle is safe to drive, proceed with caution to the nearest authorized service center.",
                assistanceRequired: response.assistance_required
                    ? "Assistance Required"
                    : "Assistance Recommended",
                faultType: response.diagnosis.fault_type || 1,
                classProbabilities: response.diagnosis.class_probabilities,
                requiredCapability: response.required_capability || "engine_repair",
            };

            setDiagnosis(diagnosisResult);
            setAssignmentId(response.assignment_id);
            setAssignedProvider(response.assigned_provider);

            let rankedProviders: Provider[] = [];

            if (response.ranked_candidates && response.ranked_candidates.length > 0) {
                rankedProviders = response.ranked_candidates.map((candidate) => {
                    const cLat = candidate.latitude || 12.9716;
                    const cLng = candidate.longitude || 77.5946;
                    const dist = candidate.distance_km && candidate.distance_km > 0
                        ? candidate.distance_km
                        : calculateDistanceKm(userLat, userLng, cLat, cLng);

                    return {
                        id: candidate.id,
                        name: candidate.name,
                        latitude: cLat,
                        longitude: cLng,
                        distanceKm: dist,
                        etaMinutes: Math.max(5, Math.round(dist * 2.5)),
                        rating: candidate.rating,
                        available: true,
                        services: candidate.capabilities && candidate.capabilities.length > 0
                            ? candidate.capabilities
                            : response.required_capability ? [response.required_capability] : ["roadside_assistance"],
                        vehicleCompatibility: candidate.vehicle_types && candidate.vehicle_types.length > 0
                            ? candidate.vehicle_types
                            : [data.vehicleType],
                        matchScore: candidate.score,
                    };
                });
            }

            // Fallback: If ranked candidates list was empty, fetch all available providers from DB with true distance
            if (rankedProviders.length === 0) {
                console.log("Fetching fallback provider directory from DB with exact distance...");
                const allProviders = await getProviders(userLat, userLng);
                rankedProviders = allProviders;
            }

            setProviders(rankedProviders);
        } catch (error) {
            console.error("Assist request failed:", error);
            try {
                const fallbackList = await getProviders(userLat, userLng);
                setProviders(fallbackList);
            } catch (fallbackError) {
                setProviders([]);
            }

            setDiagnosis({
                fault: "Rich Mixture / Engine Misfire",
                confidence: 0.95,
                severity: "High",
                safetyRecommendation: "Over-rich fuel ratio detected. Please remain stopped and request engine repair assistance.",
                assistanceRequired: "Assistance Recommended",
                requiredCapability: "engine_repair",
            });
        }

        setPage("results");
    };

    /* Handle Replan button */
    const handleReplan = async () => {
        if (!assignmentId) return;
        const userLat = breakdownData?.latitude ?? 12.9345;
        const userLng = breakdownData?.longitude ?? 77.6265;

        try {
            const replanRes = await replanAssistance(assignmentId);
            if (replanRes.assignment_id) {
                setAssignmentId(replanRes.assignment_id);
            }
            if (replanRes.assigned_provider) {
                setAssignedProvider(replanRes.assigned_provider);
            }
            if (replanRes.message) {
                setReplanMessage(replanRes.message);
            }
            if (replanRes.ranked_candidates && replanRes.ranked_candidates.length > 0) {
                const newRanked: Provider[] = replanRes.ranked_candidates.map((c) => {
                    const cLat = c.latitude || 12.9716;
                    const cLng = c.longitude || 77.5946;
                    const dist = c.distance_km && c.distance_km > 0
                        ? c.distance_km
                        : calculateDistanceKm(userLat, userLng, cLat, cLng);

                    return {
                        id: c.id,
                        name: c.name,
                        latitude: cLat,
                        longitude: cLng,
                        distanceKm: dist,
                        etaMinutes: Math.max(5, Math.round(dist * 2.5)),
                        rating: c.rating,
                        available: true,
                        services: c.capabilities && c.capabilities.length > 0
                            ? c.capabilities
                            : diagnosis?.requiredCapability ? [diagnosis.requiredCapability] : ["roadside_assistance"],
                        vehicleCompatibility: c.vehicle_types && c.vehicle_types.length > 0
                            ? c.vehicle_types
                            : breakdownData ? [breakdownData.vehicleType] : ["car"],
                        matchScore: c.score,
                    };
                });
                setProviders(newRanked);
            }
        } catch (err) {
            console.error("Replan failed:", err);
        }
    };

    if (page === "breakdown") {
        return (
            <Breakdown
                onBack={() => setPage("home")}
                onComplete={handleAnalysisComplete}
            />
        );
    }

    if (page === "results") {
        return (
            <Results
                onBack={() => setPage("breakdown")}
                providers={providers}
                diagnosis={diagnosis}
                assignmentId={assignmentId}
                assignedProvider={assignedProvider}
                replanMessage={replanMessage}
                onReplan={handleReplan}
                userLat={breakdownData?.latitude || 12.9345}
                userLng={breakdownData?.longitude || 77.6265}
                userLocationName={breakdownData?.location || "Koramangala, Bengaluru"}
                enginePhoto={breakdownData?.enginePhoto}
            />
        );
    }

    return (
        <Home
            onReport={() => setPage("breakdown")}
        />
    );
}

export default App;