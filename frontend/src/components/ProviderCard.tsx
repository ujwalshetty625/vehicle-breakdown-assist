import type { Provider } from "../types/vehicle";

interface ProviderCardProps {
    provider: Provider;
    isPrimary?: boolean;
    onCall?: (providerName: string) => void;
    onReplan?: () => void;
    isReplanning?: boolean;
}

const formatCapability = (val: string): string => {
    return val
        .replace(/_/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase());
};

export default function ProviderCard({
    provider,
    isPrimary = false,
    onCall,
    onReplan,
    isReplanning = false,
}: ProviderCardProps) {
    return (
        <div className={`results-card glass-card ${isPrimary ? "primary-provider-card" : "provider-subcard"}`}>
            {isPrimary && (
                <div className="primary-badge">🏆 TOP MATCHED PROVIDER (DATABASE VERIFIED)</div>
            )}

            <div className="provider-header-row">
                <div>
                    <h3 className="provider-name-text">{provider.name}</h3>
                    <div className="provider-sub-info">
                        <span className="rating-stars">⭐ {provider.rating.toFixed(1)} / 5.0</span>
                        <span className="info-dot">•</span>
                        <span className="distance-info">📍 {provider.distanceKm} km away</span>
                        <span className="info-dot">•</span>
                        <span className="eta-info">⏱️ ~{provider.etaMinutes || 15} mins ETA</span>
                    </div>
                </div>

                <div className="status-indicator-badge">
                    <span className="status-dot green-dot" /> Available
                </div>
            </div>

            <div className="services-tags-row">
                <span className="tags-heading">Capabilities:</span>
                {provider.services.map((srv) => (
                    <span key={srv} className="service-tag">
                        🛠️ {formatCapability(srv)}
                    </span>
                ))}
            </div>

            {provider.vehicleCompatibility && provider.vehicleCompatibility.length > 0 && (
                <div className="services-tags-row">
                    <span className="tags-heading">Supported Vehicles:</span>
                    {provider.vehicleCompatibility.map((vt) => (
                        <span key={vt} className="compatibility-tag">
                            🚗 {vt.replace(/_/g, " ")}
                        </span>
                    ))}
                </div>
            )}

            <div className="provider-actions-row">
                <button
                    type="button"
                    className="btn-call-provider"
                    onClick={() => onCall && onCall(provider.name)}
                >
                    📞 Request Assistance Now
                </button>

                {isPrimary && onReplan && (
                    <button
                        type="button"
                        className="btn-replan-provider"
                        onClick={onReplan}
                        disabled={isReplanning}
                    >
                        {isReplanning ? "🔄 Replanning..." : "🔄 Reassign Provider"}
                    </button>
                )}
            </div>
        </div>
    );
}
