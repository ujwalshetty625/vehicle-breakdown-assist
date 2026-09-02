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
                fault: response.diagnosis.fault_name,
                confidence: response.diagnosis.confidence,
                severity: response.severity?.severity
                    ? response.severity.severity.charAt(0).toUpperCase() + response.severity.severity.slice(1)
                    : "Medium",
                safeToDrive: response.severity?.safe_to_drive,
                lowConfidence: response.severity?.low_confidence,
                advisory: response.severity?.advisory,
                safetyRecommendation: response.roadside_safety?.guidance || response.severity?.advisory || "",
                roadsideSafety: response.roadside_safety,
                assistanceRequired: response.assistance_required
                    ? "Assistance Required"
                    : "No Assistance Required",
                faultType: response.diagnosis.fault_type,
                classProbabilities: response.diagnosis.class_probabilities,
                requiredCapability: response.required_capability,
            };

            setDiagnosis(diagnosisResult);
            setAssignmentId(response.assignment_id);
            setAssignedProvider(response.assigned_provider);

            let rankedProviders: Provider[] = [];

            if (response.ranked_candidates && response.ranked_candidates.length > 0) {
                rankedProviders = response.ranked_candidates.map((candidate) => {
                    const cLat = candidate.latitude || userLat;
                    const cLng = candidate.longitude || userLng;
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
                        services: candidate.capabilities || [],
                        vehicleCompatibility: candidate.vehicle_types || [],
                        matchScore: candidate.score,
                        phone: candidate.phone,
                        email: candidate.email,
                    };
                });
            }

            // Fallback: If ranked candidates list was empty, fetch all available providers from DB with true distance
            if (rankedProviders.length === 0) {
                const allProviders = await getProviders(userLat, userLng);
                rankedProviders = allProviders;
            }

            setProviders(rankedProviders);
        } catch (error) {
            console.error("Assist request failed:", error);
            alert("Backend ML assistance server error. Please ensure FastAPI uvicorn server is running at http://127.0.0.1:8000.");
            return;
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
                        services: c.capabilities || [],
                        vehicleCompatibility: c.vehicle_types || [],
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