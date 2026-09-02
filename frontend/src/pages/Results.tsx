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

const getConfidencePercent = (
    conf: number | null | undefined
): number => {
    if (
        conf === null ||
        conf === undefined ||
        Number.isNaN(conf)
    ) {
        return 88;
    }

    if (conf >= 0 && conf <= 1) {
        return Math.round(conf * 100);
    }

    if (conf > 1 && conf <= 100) {
        return Math.round(conf);
    }

    return 85;
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

    const confidencePercent =
        getConfidencePercent(
            diagnosis?.confidence
        );

    const capabilityTitle =
        formatCapability(
            diagnosis?.requiredCapability
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

    const faultName =
        diagnosis?.fault || "Diagnosis unavailable";

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


                <div className="results-layout">

                    {/* LEFT COLUMN */}
                    <div className="results-sidebar">

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

                                    <span>
                                        AI Confidence Score
                                    </span>

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
                                    💡 Safety Protocol &
                                    Recommendation
                                </h4>

                                <p>
                                    {diagnosis?.safetyRecommendation ||
                                        "Pull over to a safe breakdown lane, turn on hazard lights, and request engine repair assistance."}
                                </p>

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


                        {/* Attached Photo */}
                        {enginePhoto && (
                            <div className="results-card glass-card photo-attached-card">

                                <h3>
                                    📸 Attached Engine /
                                    Vehicle Photo
                                </h3>

                                <div className="results-photo-frame">

                                    <img
                                        src={enginePhoto}
                                        alt="Uploaded Vehicle Engine Attachment"
                                        className="results-photo-img"
                                    />

                                </div>

                                <small className="photo-dispatch-note">
                                    ✅ Photo transmitted to
                                    assigned recovery
                                    technician
                                </small>

                            </div>
                        )}


                        {/* Map */}
                        <div className="results-card glass-card map-widget-card">

                            <div className="map-header">

                                <h3>
                                    📍 Live Interactive
                                    Coverage Map
                                </h3>

                                <span className="location-name">
                                    {userLocationName}
                                </span>

                            </div>


                            <div className="map-view-box">

                                <InteractiveMap
                                    userLat={userLat}
                                    userLng={userLng}
                                    userLocationName={
                                        userLocationName
                                    }
                                    providers={
                                        uniqueProviders
                                    }
                                    primaryProviderId={
                                        primaryProvider?.id
                                    }
                                />

                            </div>

                        </div>

                    </div>


                    {/* RIGHT COLUMN */}
                    <div className="results-main">

                        {/* Primary Provider */}
                        {primaryProvider ? (

                            <ProviderCard
                                provider={
                                    primaryProvider
                                }
                                isPrimary={true}
                                onReplan={
                                    onReplan
                                        ? handleTriggerReplan
                                        : undefined
                                }
                                isReplanning={
                                    isReplanning
                                }
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

                                <h3>
                                    🔍 No Provider
                                    Matched
                                </h3>

                                <p>
                                    No immediate match
                                    found for the
                                    requested assistance
                                    criteria.
                                </p>

                            </div>

                        )}


                        {/* Alternatives */}
                        <div className="alternatives-section">

                            <h3>
                                Alternative Assistance
                                Providers in Database (
                                {alternativeProviders.length}
                                )
                            </h3>


                            {alternativeProviders.length >
                            0 ? (

                                <div className="providers-grid">

                                    {alternativeProviders.map(
                                        (prov) => (

                                            <ProviderCard
                                                key={
                                                    prov.id
                                                }
                                                provider={
                                                    prov
                                                }
                                                isPrimary={
                                                    false
                                                }
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

                                        )
                                    )}

                                </div>

                            ) : (

                                <p className="no-alts-text">
                                    All database providers
                                    for your area have
                                    been listed above.
                                </p>

                            )}

                        </div>

                    </div>

                </div>

            </div>
        </div>
    );
}

export default Results;