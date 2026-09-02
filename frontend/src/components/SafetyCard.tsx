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
    const rawSeverity = (severityInfo?.severity || "medium").toLowerCase();
    const severity = severityInfo?.severity || rawSeverity;
    
    // Determine safeToDrive: false if severity is high/critical or backend says false
    const safeToDrive = severityInfo?.safe_to_drive !== undefined
        ? severityInfo.safe_to_drive
        : (rawSeverity !== "high" && rawSeverity !== "critical");

    // Determine riskLevel: elevated/high if safeToDrive is false or backend says elevated/high/critical
    const riskLevel = roadsideSafety?.risk_level
        ? roadsideSafety.risk_level
        : (!safeToDrive || rawSeverity === "high" || rawSeverity === "critical" ? "high" : "low");

    const guidance = roadsideSafety?.guidance
        || (!safeToDrive
            ? "Do not continue driving. Prioritize waiting safely for assistance. Keep hazard lights on and remain visible while waiting."
            : "Vehicle can be operated with caution to the nearest authorized repair facility. Drive at low speed.");

    const etaEstimate = roadsideSafety?.eta_estimate || "15-25 min";
    const isNight = roadsideSafety?.is_night ?? false;

    const getRiskColorClass = (risk: string) => {
        switch (risk.toLowerCase()) {
            case "critical":
                return "risk-critical";
            case "high":
            case "elevated":
                return "risk-high";
            case "medium":
            case "moderate":
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

                <div className="safety-actions-box" style={{ background: "#f8fafc", padding: "10px 12px", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
                    <span style={{ fontSize: "0.725rem", color: "#64748b", fontWeight: "700", textTransform: "uppercase", display: "block", marginBottom: "6px" }}>
                        ⚡ Recommended Safety Checklist
                    </span>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px", fontSize: "0.775rem", color: "#334155" }}>
                        <span>⚠️ Turn on Hazard Lights</span>
                        <span>🛡️ Remain in safe location</span>
                        <span>🦺 Stay visible to traffic</span>
                        <span>📱 Keep emergency phone ready</span>
                    </div>
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

            </div>
        </div>
    );
}
