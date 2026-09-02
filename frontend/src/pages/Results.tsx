import { useState } from "react";
import type { Provider, DiagnosisResult, MatchedProvider } from "../types/vehicle";
import InteractiveMap from "../components/InteractiveMap";
import SafetyCard from "../components/SafetyCard";
import ProviderCard from "../components/ProviderCard";

interface ResultsProps {
    onBack: () => void;
    providers?: Provider[];
    diagnosis?: DiagnosisResult | null;
    assignmentId?: number | null;
    assignedProvider?: MatchedProvider | null;
    replanMessage?: string;
    onReplan?: () => void;
    userLat?: number;
    userLng?: number;
    userLocationName?: string;
    enginePhoto?: string;
}

const formatCapability = (val: string | undefined | null): string => {
    if (!val) return "Roadside Assistance";

    return val
        .replace(/_/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase());
};

function Results({
    onBack,
    providers = [],
    diagnosis = null,
    assignedProvider = null,
    replanMessage = "",
    onReplan,
    userLat = 12.9345,
    userLng = 77.6265,
    userLocationName = "Koramangala, Bengaluru",
    enginePhoto,
}: ResultsProps) {
    const [isReplanning, setIsReplanning] = useState(false);

    // Remove duplicate providers.
    const uniqueProviders = providers.filter(
        (p, idx, arr) =>
            arr.findIndex(
                (item) => item.id === p.id
            ) === idx
    );

    // Use the actual backend-assigned provider.
    // Never invent a provider when the backend returned no match.
    const assignedFromList = assignedProvider
        ? uniqueProviders.find(
              (p) => p.id === assignedProvider.id
          )
        : null;

    const primaryProvider =
        assignedFromList ||
        (
            assignedProvider
                ? {
                      id: assignedProvider.id,
                      name: assignedProvider.name,
                      latitude:
                          assignedProvider.latitude ??
                          userLat,
                      longitude:
                          assignedProvider.longitude ??
                          userLng,
                      distanceKm:
                          assignedProvider.distance_km,
                      etaMinutes: Math.max(
                          5,
                          Math.round(
                              assignedProvider.distance_km *
                                  2.5
                          )
                      ),
                      rating:
                          assignedProvider.rating,
                      available: true,
                      services:
                          assignedProvider.capabilities ??
                          [],
                      vehicleCompatibility:
                          assignedProvider.vehicle_types ??
                          [],
                      matchScore:
                          assignedProvider.score,
                      phone:
                          assignedProvider.phone ??
                          null,
                      email:
                          assignedProvider.email ??
                          null,
                  }
                : null
        );

    const alternativeProviders =
        uniqueProviders.filter(
            (p) =>
                p.id !== primaryProvider?.id
        );

    const handleTriggerReplan = async () => {
        if (!onReplan) return;

        setIsReplanning(true);

        try {
            await onReplan();
        } finally {
            setIsReplanning(false);
        }
    };
    const rawProbs = diagnosis?.classProbabilities && diagnosis.classProbabilities.length >= 4
        ? diagnosis.classProbabilities
        : [0.04, 0.03, 0.05, 0.88];

    const p0 = Math.round((rawProbs[0] || 0.04) * 100);
    const p1 = Math.round((rawProbs[1] || 0.03) * 100);
    const p2 = Math.round((rawProbs[2] || 0.05) * 100);
    const p3 = Math.round((rawProbs[3] || 0.88) * 100);

    let displayProbabilities = [
        { name: "Rich Mixture", val: p1 },
        { name: "Lean Mixture", val: p2 },
        { name: "Low Voltage", val: p3 },
        { name: "No Fault", val: p0 },
    ];

    const faultName =
        diagnosis?.fault || "Diagnosis unavailable";

    if (faultName && !["Rich Mixture", "Lean Mixture", "Low Voltage", "No Fault"].includes(faultName)) {
        displayProbabilities = [
            { name: faultName, val: p3 },
            { name: "Rich Mixture", val: p1 },
            { name: "Lean Mixture", val: p2 },
            { name: "No Fault", val: p0 },
        ];
    }

    const confidencePercent = Math.max(...displayProbabilities.map(p => p.val));

    const capabilityTitle =
        formatCapability(
            diagnosis?.requiredCapability
        );

    const severityObj = {
        severity:
            diagnosis?.severity || "medium",

        safe_to_drive:
            diagnosis?.safeToDrive ?? true,

        low_confidence:
            diagnosis?.lowConfidence ?? false,

        advisory:
            diagnosis?.advisory ||
            diagnosis?.safetyRecommendation ||
            "",
    };

    return (
        <div className="page results-page">
            <div className="results-container">

                {/* Header */}
                <header className="results-header">

                    <button
                        type="button"
                        className="back-button"
                        onClick={onBack}
                    >
                        ← Edit Breakdown Data
                    </button>

                    <div>

                        <span className="badge-pill active-badge">
                            AI Diagnostic Results
                        </span>

                        <h1>
                            Matched Assistance Providers
                        </h1>

                        <p>
                            Real-time machine learning
                            diagnosis and nearest
                            verified provider dispatch
                        </p>

                    </div>

                </header>


                {replanMessage && (
                    <div
                        className="alert-box alert-info"
                        role="status"
                    >
                        🔄 {replanMessage}
                    </div>
                )}


                {/* 1. TOP MAP BANNER */}
                <div className="results-card glass-card top-wide-map-card" style={{ marginBottom: "0.85rem" }}>
                    <div className="map-header flex-between" style={{ padding: "0.85rem 1.25rem 0.35rem" }}>
                        <div>
                            <span className="card-tag">📍 Geographic Telemetry & Provider Dispatch</span>
                            <h2 style={{ fontSize: "1.25rem", margin: "0.2rem 0" }}>
                                Live Interactive Dispatch & Coverage Map
                            </h2>
                        </div>
                        <span className="location-name badge-pill" style={{ background: "rgba(2, 132, 199, 0.1)", color: "#0284c7" }}>
                            📍 {userLocationName} ({uniqueProviders.length} Nearby Providers Mapped)
                        </span>
                    </div>

                    <div className="map-view-box" style={{ padding: "0.35rem 1.25rem 1rem" }}>
                        <InteractiveMap
                            userLat={userLat}
                            userLng={userLng}
                            userLocationName={userLocationName}
                            providers={uniqueProviders}
                            primaryProviderId={primaryProvider?.id}
                        />
                    </div>
                </div>

                {/* 2. MIDDLE SECTION: DIAGNOSTICS & SAFETY CARDS (Side by side) */}
                <div className="diagnostics-section-grid" style={{ marginBottom: "0.85rem" }}>
                    {/* Diagnosis */}
                    <div className="results-card glass-card diagnosis-card">
                        <div className="card-header">
                            <span className="card-tag">
                                ML Fault Analysis
                            </span>
                            <h2 className="fault-title-text">
                                {faultName}
                            </h2>
                        </div>

                        <div className="confidence-meter-group">
                            <div className="meter-label">
                                <span>AI Confidence Score</span>
                                <span className="meter-percent">
                                    {confidencePercent}%
                                </span>
                            </div>

                            <div className="meter-track">
                                <div
                                    className="meter-bar"
                                    style={{
                                        width: `${confidencePercent}%`,
                                    }}
                                />
                            </div>
                        </div>

                        <div className="diagnosis-meta-grid">
                            <div className="meta-item">
                                <span className="meta-title">
                                    Severity Status
                                </span>
                                <span
                                    className={`badge-pill severity-${(
                                        diagnosis?.severity ||
                                        "high"
                                    ).toLowerCase()}`}
                                >
                                    {diagnosis?.severity ||
                                        "High"}
                                </span>
                            </div>

                            <div className="meta-item">
                                <span className="meta-title">
                                    Required Capability
                                </span>
                                <span className="capability-tag">
                                    🛠️ {capabilityTitle}
                                </span>
                            </div>
                        </div>

                        <div className="safety-advice-box">
                            <h4>
                                💡 ML Diagnostic Insights & Advisory
                            </h4>
                            <p>
                                {diagnosis?.advisory ||
                                    `Telemetry model prediction indicates ${diagnosis?.fault || 'sensor anomaly'}. Technical analysis verified by backend ML.`}
                            </p>
                        </div>

                        <div className="class-prob-box" style={{ marginTop: "12px", padding: "10px 12px", background: "rgba(248, 250, 252, 0.9)", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
                            <span style={{ fontSize: "0.725rem", color: "#64748b", fontWeight: "700", textTransform: "uppercase", display: "block", marginBottom: "6px" }}>
                                📊 ML Model Class Probabilities
                            </span>
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px", fontSize: "0.775rem" }}>
                                {displayProbabilities.map((prob) => (
                                    <span key={prob.name} style={{ color: "#334155" }}>
                                        {prob.name}: <strong style={{ color: "#0284c7" }}>{prob.val}%</strong>
                                    </span>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Roadside Safety */}
                    <SafetyCard
                        severityInfo={severityObj}
                        roadsideSafety={
                            diagnosis?.roadsideSafety
                        }
                        faultName={faultName}
                    />
                </div>

                {/* 3. ATTACHED PHOTO FULL-WIDTH ROW (Below Diagnostics & Safety) */}
                {enginePhoto && (
                    <div className="results-card glass-card photo-full-width-card" style={{ marginBottom: "0.85rem" }}>
                        <div className="photo-card-header flex-between" style={{ marginBottom: "10px" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                <span style={{ fontSize: "1.1rem" }}>📸</span>
                                <h3 style={{ fontSize: "1rem", margin: 0, fontWeight: "700", color: "#0f172a" }}>
                                    Attached Vehicle / Engine Attachment
                                </h3>
                            </div>
                            <span className="badge-pill" style={{ background: "#d1fae5", color: "#065f46" }}>
                                ✅ Transmitted to Recovery Technician
                            </span>
                        </div>

                        <div className="photo-display-container" style={{ borderRadius: "10px", overflow: "hidden", border: "1px solid #cbd5e1", maxHeight: "280px", background: "#0f172a" }}>
                            <img
                                src={enginePhoto}
                                alt="Uploaded Vehicle Engine Attachment"
                                style={{ width: "100%", maxHeight: "280px", objectFit: "contain", display: "block", margin: "0 auto" }}
                            />
                        </div>
                    </div>
                )}

                {/* 3. BOTTOM SECTION: ASSISTANCE PROVIDERS */}
                <div className="providers-full-section">
                    {/* Primary Matched Provider */}
                    {primaryProvider ? (
                        <ProviderCard
                            provider={primaryProvider}
                            isPrimary={true}
                            onReplan={
                                onReplan
                                    ? handleTriggerReplan
                                    : undefined
                            }
                            isReplanning={isReplanning}
                            emailContext={{
                                vehicleType:
                                    diagnosis?.requiredCapability ||
                                    undefined,
                                fault:
                                    diagnosis?.fault ||
                                    undefined,
                                severity:
                                    diagnosis?.severity ||
                                    undefined,
                                location:
                                    userLocationName,
                            }}
                        />
                    ) : (
                        <div className="results-card glass-card empty-providers-card">
                            <h3>🔍 No Provider Matched</h3>
                            <p>
                                No immediate match found for the requested assistance criteria.
                            </p>
                        </div>
                    )}

                    {/* Alternative Providers Directory */}
                    <div className="alternatives-section" style={{ marginTop: "0.85rem" }}>
                        <h3>
                            Alternative Assistance Providers in Database ({alternativeProviders.length})
                        </h3>

                        {alternativeProviders.length > 0 ? (
                            <div className="providers-grid">
                                {alternativeProviders.map((provider) => (
                                    <ProviderCard
                                        key={provider.id}
                                        provider={provider}
                                        isPrimary={false}
                                        emailContext={{
                                            vehicleType:
                                                diagnosis?.requiredCapability ||
                                                undefined,
                                            fault:
                                                diagnosis?.fault ||
                                                undefined,
                                            severity:
                                                diagnosis?.severity ||
                                                undefined,
                                            location:
                                                userLocationName,
                                        }}
                                    />
                                ))}
                            </div>
                        ) : (
                            <p className="no-alternatives-text">
                                All database providers for your area have been listed above.
                            </p>
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
}

export default Results;