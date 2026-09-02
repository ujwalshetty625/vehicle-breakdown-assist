import type { Provider } from "../types/vehicle";

interface ProviderCardProps {
    provider: Provider;
    isPrimary?: boolean;
    onReplan?: () => void;
    isReplanning?: boolean;
    emailContext?: {
        vehicleType?: string;
        fault?: string;
        severity?: string;
        location?: string;
    };
}

const formatCapability = (val: string): string =>
    val.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());

const mailto = (provider: Provider, ctx: ProviderCardProps["emailContext"]) => {
    const subject = `Roadside Assistance Request - ${provider.name}`;
    const body = [
        "Hello,",
        "",
        "I need roadside assistance for my vehicle.",
        ctx?.vehicleType ? `Vehicle type: ${ctx.vehicleType}` : "",
        ctx?.fault ? `Detected fault: ${ctx.fault}` : "",
        ctx?.severity ? `Severity: ${ctx.severity}` : "",
        ctx?.location ? `Breakdown location: ${ctx.location}` : "",
        provider.distanceKm != null ? `Provider distance: ${provider.distanceKm} km` : "",
        "",
        "Please contact me regarding assistance availability."
    ].filter(Boolean).join("\n");
    return `mailto:${provider.email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
};

export default function ProviderCard({
    provider, isPrimary = false, onReplan, isReplanning = false, emailContext
}: ProviderCardProps) {
    const canCall = Boolean(provider.phone);
    const canEmail = Boolean(provider.email);

    return (
        <div className={`results-card glass-card ${isPrimary ? "primary-provider-card" : "provider-subcard"}`}>
            {isPrimary && <div className="primary-badge">🏆 TOP MATCHED PROVIDER (DATABASE VERIFIED)</div>}

            <div className="provider-header-row">
                <div>
                    <h3 className="provider-name-text">{provider.name}</h3>
                    <div className="provider-sub-info">
                        <span className="rating-stars">⭐ {provider.rating.toFixed(1)} / 5.0</span>
                        <span className="info-dot">•</span>
                        <span className="distance-info">📍 {provider.distanceKm} km away</span>
                        <span className="info-dot">•</span>
                        <span className="eta-info">⏱️ ~{provider.etaMinutes || Math.max(5, Math.round(provider.distanceKm * 2.5))} mins ETA</span>
                    </div>
                </div>
                <div className={`status-indicator-badge ${provider.available ? "" : "status-unavailable"}`}>
                    <span className={`status-dot ${provider.available ? "green-dot" : ""}`} />
                    {provider.available ? "Available" : "Unavailable"}
                </div>
            </div>

            <div className="services-tags-row">
                <span className="tags-heading">Capabilities:</span>
                {provider.services.map(srv =>
                    <span key={srv} className="service-tag">🛠️ {formatCapability(srv)}</span>
                )}
            </div>

            {provider.vehicleCompatibility.length > 0 && (
                <div className="services-tags-row">
                    <span className="tags-heading">Supported Vehicles:</span>
                    {provider.vehicleCompatibility.map(vt =>
                        <span key={vt} className="compatibility-tag">🚗 {vt.replace(/_/g, " ")}</span>
                    )}
                </div>
            )}

            <div className="provider-actions-row">
                {canCall && provider.available ? (
                    <a className="btn-call-provider" href={`tel:${provider.phone}`}>
                        📞 Call Provider Now
                    </a>
                ) : (
                    <button type="button" className="btn-call-provider" disabled>
                        📞 {canCall ? "Provider Unavailable" : "Call Unavailable"}
                    </button>
                )}

                {canEmail && provider.available && (
                    <a className="btn-email-provider" href={mailto(provider, emailContext)}>
                        ✉️ Contact via Email
                    </a>
                )}

                {isPrimary && onReplan && (
                    <button type="button" className="btn-replan-provider"
                        onClick={onReplan} disabled={isReplanning}>
                        {isReplanning ? "🔄 Replanning..." : "🔄 Reassign Provider"}
                    </button>
                )}
            </div>
        </div>
    );
}
