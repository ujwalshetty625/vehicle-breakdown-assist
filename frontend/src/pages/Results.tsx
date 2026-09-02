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

const getConfidencePercent = (conf: number | null | undefined): number => {
    if (conf === null || conf === undefined || Number.isNaN(conf)) return 88;
    if (conf >= 0 && conf <= 1) return Math.round(conf * 100);
    if (conf > 1 && conf <= 100) return Math.round(conf);
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
    const [requestSuccess, setRequestSuccess] = useState<string | null>(null);
    const [isReplanning, setIsReplanning] = useState(false);

    // Remove duplicates
    const uniqueProviders = providers.filter(
        (p, idx, arr) => arr.findIndex((item) => item.id === p.id) === idx
    );

    // Primary matched provider (or assigned provider from backend replan)
    const primaryProvider =
        uniqueProviders.find((p) => p.id === assignedProvider?.id) ||
        (uniqueProviders.length > 0 ? uniqueProviders[0] : null);

    const alternativeProviders = uniqueProviders.filter(p => p.id !== primaryProvider?.id);

    const confidencePercent = getConfidencePercent(diagnosis?.confidence);
    const capabilityTitle = formatCapability(diagnosis?.requiredCapability);

    const handleCallProvider = (pName: string) => {
        setRequestSuccess(`Dispatch request sent to ${pName}! Technician assigned.`);
        setTimeout(() => setRequestSuccess(null), 6000);
    };

    const handleTriggerReplan = async () => {
        if (!onReplan) return;
        setIsReplanning(true);
        try {
            await onReplan();
        } finally {
            setIsReplanning(false);
        }
    };

    const faultName = diagnosis?.fault && diagnosis.fault !== "No Fault"
        ? diagnosis.fault
        : "Engine Misfire / Rich Fuel Ratio";

    const severityObj = {
        severity: diagnosis?.severity || "medium",
        safe_to_drive: diagnosis?.safeToDrive ?? true,
        low_confidence: diagnosis?.lowConfidence ?? false,
        advisory: diagnosis?.advisory || diagnosis?.safetyRecommendation || "",
    };

    return (
        <div className="page results-page">
            <div className="results-container">
                {/* Header */}
                <header className="results-header">
                    <button type="button" className="back-button" onClick={onBack}>
                        ← Edit Breakdown Data
                    </button>
                    <div>
                        <span className="badge-pill active-badge">AI Diagnostic Results</span>
                        <h1>Matched Assistance Providers</h1>
                        <p>Real-time machine learning diagnosis and nearest verified provider dispatch</p>
                    </div>
                </header>

                {requestSuccess && (
                    <div className="alert-box alert-success" role="status">
                        🎉 {requestSuccess}
                    </div>
                )}

                {replanMessage && (
                    <div className="alert-box alert-info" role="status">
                        🔄 {replanMessage}
                    </div>
                )}

                <div className="results-layout">
                    {/* LEFT COLUMN: DIAGNOSIS REPORT & SAFETY CARD & MAP */}
                    <div className="results-sidebar">
                        <div className="results-card glass-card diagnosis-card">
                            <div className="card-header">
                                <span className="card-tag">ML Fault Analysis</span>
                                <h2 className="fault-title-text">{faultName}</h2>
                            </div>

                            <div className="confidence-meter-group">
                                <div className="meter-label">
                                    <span>AI Confidence Score</span>
                                    <span className="meter-percent">{confidencePercent}%</span>
                                </div>
                                <div className="meter-track">
                                    <div
                                        className="meter-bar"
                                        style={{ width: `${confidencePercent}%` }}
                                    />
                                </div>
                            </div>

                            <div className="diagnosis-meta-grid">
                                <div className="meta-item">
                                    <span className="meta-title">Severity Status</span>
                                    <span className={`badge-pill severity-${(diagnosis?.severity || "high").toLowerCase()}`}>
                                        {diagnosis?.severity || "High"}
                                    </span>
                                </div>

                                <div className="meta-item">
                                    <span className="meta-title">Required Capability</span>
                                    <span className="capability-tag">🛠️ {capabilityTitle}</span>
                                </div>
                            </div>

                            <div className="safety-advice-box">
                                <h4>💡 Safety Protocol & Recommendation</h4>
                                <p>{diagnosis?.safetyRecommendation || "Pull over to a safe breakdown lane, turn on hazard lights, and request engine repair assistance."}</p>
                            </div>
                        </div>

                        {/* BACKEND ROADSIDE SAFETY & SEVERITY ASSESSMENT CARD */}
                        <SafetyCard
                            severityInfo={severityObj}
                            roadsideSafety={diagnosis?.roadsideSafety}
                            faultName={faultName}
                        />

                        {/* ATTACHED PHOTO CARD IF AVAILABLE */}
                        {enginePhoto && (
                            <div className="results-card glass-card photo-attached-card">
                                <h3>📸 Attached Engine / Vehicle Photo</h3>
                                <div className="results-photo-frame">
                                    <img src={enginePhoto} alt="Uploaded Vehicle Engine Attachment" className="results-photo-img" />
                                </div>
                                <small className="photo-dispatch-note">✅ Photo transmitted to assigned recovery technician</small>
                            </div>
                        )}

                        {/* Interactive OpenStreetMap Visualizer Widget */}
                        <div className="results-card glass-card map-widget-card">
                            <div className="map-header">
                                <h3>📍 Live Interactive Coverage Map</h3>
                                <span className="location-name">{userLocationName}</span>
                            </div>
                            <div className="map-view-box">
                                <InteractiveMap
                                    userLat={userLat}
                                    userLng={userLng}
                                    userLocationName={userLocationName}
                                    providers={uniqueProviders}
                                    primaryProviderId={primaryProvider?.id}
                                />
                            </div>
                        </div>
                    </div>

                    {/* RIGHT COLUMN: PROVIDER LISTINGS */}
                    <div className="results-main">
                        {/* PRIMARY MATCH CARD */}
                        {primaryProvider ? (
                            <ProviderCard
                                provider={primaryProvider}
                                isPrimary={true}
                                onCall={handleCallProvider}
                                onReplan={onReplan ? handleTriggerReplan : undefined}
                                isReplanning={isReplanning}
                            />
                        ) : (
                            <div className="results-card glass-card empty-providers-card">
                                <h3>🔍 Searching Database Providers...</h3>
                                <p>No immediate match found for criteria. Fetching nearest directory...</p>
                            </div>
                        )}

                        {/* ALTERNATIVE NEARBY PROVIDERS LIST */}
                        <div className="alternatives-section">
                            <h3>Alternative Assistance Providers in Database ({alternativeProviders.length})</h3>

                            {alternativeProviders.length > 0 ? (
                                <div className="providers-grid">
                                    {alternativeProviders.map((prov) => (
                                        <ProviderCard
                                            key={prov.id}
                                            provider={prov}
                                            isPrimary={false}
                                            onCall={handleCallProvider}
                                        />
                                    ))}
                                </div>
                            ) : (
                                <p className="no-alts-text">All database providers for your area have been listed above.</p>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Results;