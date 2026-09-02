import type { SeverityInfo, RoadsideSafetyInfo } from "../types/vehicle";

interface SafetyCardProps {
    severityInfo?: SeverityInfo;
    roadsideSafety?: RoadsideSafetyInfo;
    faultName?: string;
}

export default function SafetyCard({
    severityInfo,
    roadsideSafety,
    faultName = "Detected Fault",
}: SafetyCardProps) {
    const severity = severityInfo?.severity || "medium";
    const safeToDrive = severityInfo?.safe_to_drive ?? true;
    const riskLevel = roadsideSafety?.risk_level || "low";
    const guidance = roadsideSafety?.guidance || severityInfo?.advisory || "Exercise caution on roadside.";
    const etaEstimate = roadsideSafety?.eta_estimate || "15-25 min";
    const contextNote = roadsideSafety?.context_note || "";
    const isNight = roadsideSafety?.is_night ?? false;

    const getRiskColorClass = (risk: string) => {
        switch (risk.toLowerCase()) {
            case "critical":
                return "risk-critical";
            case "high":
                return "risk-high";
            case "medium":
                return "risk-medium";
            default:
                return "risk-low";
        }
    };

    return (
        <div className="results-card glass-card roadside-safety-card">
            <div className="card-header flex-between">
                <div>
                    <span className="card-tag">🛡️ Backend Safety Protocol</span>
                    <h2>Roadside Safety Assessment</h2>
                </div>
                <div className="safety-badges-group">
                    <span className={`badge-pill ${getRiskColorClass(riskLevel)}`}>
                        Risk: {riskLevel.toUpperCase()}
                    </span>
                    <span className={`badge-pill ${safeToDrive ? "badge-safe" : "badge-unsafe"}`}>
                        {safeToDrive ? "🟢 Safe to Drive Short Distances" : "🔴 DO NOT DRIVE — Pull Over"}
                    </span>
                </div>
            </div>

            <div className="safety-content-body">
                <div className="guidance-box">
                    <h4>📋 Safety Guidance</h4>
                    <p className="guidance-text">{guidance}</p>
                </div>

                <div className="safety-meta-grid">
                    <div className="safety-meta-item">
                        <span className="meta-label">Estimated Provider ETA</span>
                        <span className="meta-val">⏱️ {etaEstimate}</span>
                    </div>

                    <div className="safety-meta-item">
                        <span className="meta-label">Severity Grade</span>
                        <span className="meta-val text-capitalize">⚠️ {severity}</span>
                    </div>

                    <div className="safety-meta-item">
                        <span className="meta-label">Time & Visibility</span>
                        <span className="meta-val">
                            {isNight ? "🌙 Nighttime (High Hazard)" : "☀️ Daytime Visibility"}
                        </span>
                    </div>

                    <div className="safety-meta-item">
                        <span className="meta-label">Primary Fault</span>
                        <span className="meta-val">🔧 {faultName}</span>
                    </div>
                </div>

                {contextNote && (
                    <div className="context-note-banner">
                        <span className="note-icon">💡</span>
                        <span className="note-text">{contextNote}</span>
                    </div>
                )}
            </div>
        </div>
    );
}
