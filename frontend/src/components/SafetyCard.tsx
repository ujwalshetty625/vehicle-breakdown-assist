import type { SeverityInfo, RoadsideSafetyInfo } from "../types/vehicle";
import {
    ShieldCheck,
    ShieldAlert,
    CheckCircle2,
    AlertTriangle,
    Clock,
    Moon,
    Sun,
    Sunset,
    Wrench,
    FileText,
    PhoneCall,
    Eye,
} from "lucide-react";

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
    
    // Backend time context (day | evening | night)
    const timeContext = (roadsideSafety?.time_context || (roadsideSafety?.is_night ? "night" : "day")).toLowerCase();

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
                    <span className="card-tag flex items-center gap-1">
                        <ShieldCheck className="w-3.5 h-3.5 text-sky-600 inline mr-1" /> Safety Protocol
                    </span>
                    <h2>Roadside Safety Assessment</h2>
                </div>
                <div className="safety-badges-group">
                    <span className={`badge-pill ${getRiskColorClass(riskLevel)}`}>
                        Risk: {riskLevel.toUpperCase()}
                    </span>
                    <span className={`badge-pill ${safeToDrive ? "badge-safe" : "badge-unsafe"}`}>
                        {safeToDrive ? (
                            <>
                                <CheckCircle2 className="w-3.5 h-3.5 inline mr-1 text-emerald-600" /> Safe to Drive Short Distances
                            </>
                        ) : (
                            <>
                                <ShieldAlert className="w-3.5 h-3.5 inline mr-1 text-red-600" /> DO NOT DRIVE — Pull Over
                            </>
                        )}
                    </span>
                </div>
            </div>

            <div className="safety-content-body">
                <div className="guidance-box">
                    <h4 className="flex items-center gap-1.5">
                        <FileText className="w-4 h-4 text-sky-600 inline mr-1" /> Safety Guidance
                    </h4>
                    <p className="guidance-text">{guidance}</p>
                </div>

                {timeContext === "night" && (
                    <div style={{ background: "rgba(99, 102, 241, 0.08)", padding: "8px 12px", borderRadius: "8px", border: "1px solid rgba(99, 102, 241, 0.2)", fontSize: "0.775rem", color: "#3730a3", display: "flex", alignItems: "center", gap: "8px", marginBottom: "10px" }}>
                        <Moon className="w-4 h-4 text-indigo-600 shrink-0" />
                        <span>Nighttime breakdowns may involve increased roadside safety risk. Prioritize assistance and remain in a safe location.</span>
                    </div>
                )}

                <div className="safety-actions-box" style={{ background: "#f8fafc", padding: "10px 12px", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
                    <span style={{ fontSize: "0.725rem", color: "#64748b", fontWeight: "700", textTransform: "uppercase", display: "block", marginBottom: "6px" }}>
                        Recommended Safety Checklist
                    </span>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px", fontSize: "0.775rem", color: "#334155" }}>
                        <span><AlertTriangle className="w-3.5 h-3.5 inline mr-1 text-amber-500" /> Turn on Hazard Lights</span>
                        <span><ShieldCheck className="w-3.5 h-3.5 inline mr-1 text-emerald-600" /> Remain in safe location</span>
                        <span><Eye className="w-3.5 h-3.5 inline mr-1 text-sky-600" /> Stay visible to traffic</span>
                        <span><PhoneCall className="w-3.5 h-3.5 inline mr-1 text-indigo-600" /> Keep emergency phone ready</span>
                    </div>
                </div>

                <div className="safety-meta-grid">
                    <div className="safety-meta-item">
                        <span className="meta-label">Estimated Provider ETA</span>
                        <span className="meta-val flex items-center gap-1">
                            <Clock className="w-3.5 h-3.5 text-sky-600 inline mr-1" /> {etaEstimate}
                        </span>
                    </div>

                    <div className="safety-meta-item">
                        <span className="meta-label">Severity Grade</span>
                        <span className="meta-val text-capitalize flex items-center gap-1">
                            <AlertTriangle className="w-3.5 h-3.5 text-amber-500 inline mr-1" /> {severity}
                        </span>
                    </div>

                    <div className="safety-meta-item">
                        <span className="meta-label">Roadside Time Context</span>
                        <span className="meta-val flex items-center gap-1">
                            {timeContext === "night" ? (
                                <>
                                    <Moon className="w-3.5 h-3.5 text-indigo-500 inline mr-1" /> Night (Elevated Priority)
                                </>
                            ) : timeContext === "evening" ? (
                                <>
                                    <Sunset className="w-3.5 h-3.5 text-amber-600 inline mr-1" /> Evening (Approaching Night)
                                </>
                            ) : (
                                <>
                                    <Sun className="w-3.5 h-3.5 text-amber-500 inline mr-1" /> Day (Normal Conditions)
                                </>
                            )}
                        </span>
                    </div>

                    <div className="safety-meta-item">
                        <span className="meta-label">Primary Fault</span>
                        <span className="meta-val flex items-center gap-1">
                            <Wrench className="w-3.5 h-3.5 text-slate-600 inline mr-1" /> {faultName}
                        </span>
                    </div>
                </div>

            </div>
        </div>
    );
}

