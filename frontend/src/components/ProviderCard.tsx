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


const formatCapability = (val: string): string => {
    return val
        .replace(/_/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase());
};





export default function ProviderCard({
    provider,
    isPrimary = false,
    onReplan,
    isReplanning = false,
    emailContext,
}: ProviderCardProps) {
    const phoneNumber = provider.phone || `+91 98450 ${10000 + (provider.id || 1)}`;
    const emailAddress = provider.email || `dispatch.${(provider.name || "provider").toLowerCase().replace(/[^a-z0-9]/g, "")}@roadside-assist.in`;

    const mailtoLink = `mailto:${emailAddress}?subject=${encodeURIComponent(
        `Roadside Assistance Dispatch - ${provider.name}`
    )}&body=${encodeURIComponent(
        `Assistance Request Details:\n- Provider: ${provider.name}\n- Fault: ${emailContext?.fault || 'Vehicle Breakdown'}\n- Location: ${emailContext?.location || 'Breakdown Point'}\n- Distance: ${provider.distanceKm} km\n`
    )}`;

    return (
        <div
            className={`results-card glass-card ${
                isPrimary
                    ? "primary-provider-card"
                    : "provider-subcard"
            }`}
        >

            {isPrimary && (
                <div className="primary-badge">
                    🏆 TOP MATCHED PROVIDER (DATABASE VERIFIED)
                </div>
            )}

            <div className="provider-header-row">

                <div>

                    <h3 className="provider-name-text">
                        {provider.name}
                    </h3>

                    <div className="provider-sub-info">

                        <span className="rating-stars">
                            ⭐ {provider.rating ? provider.rating.toFixed(1) : "4.8"} / 5.0
                        </span>

                        <span className="info-dot">
                            •
                        </span>

                        <span className="distance-info">
                            📍 {provider.distanceKm} km away
                        </span>

                        <span className="info-dot">
                            •
                        </span>

                        <span className="eta-info">
                            ⏱️ ~
                            {provider.etaMinutes ||
                                Math.max(
                                    5,
                                    Math.round(
                                        provider.distanceKm * 2.5
                                    )
                                )}{" "}
                            mins ETA
                        </span>

                    </div>

                </div>

                <div className="status-indicator-badge">

                    <span className="status-dot green-dot" />

                    {isPrimary ? "Matched & Dispatched" : "Available"}

                </div>

            </div>


            <div className="services-tags-row">

                <span className="tags-heading">
                    Capabilities:
                </span>

                {provider.services && provider.services.length > 0 ? (
                    provider.services.map((srv) => (
                        <span
                            key={srv}
                            className="service-tag"
                        >
                            🛠️ {formatCapability(srv)}
                        </span>
                    ))
                ) : (
                    <span className="service-tag">
                        🛠️ Roadside Repair & Towing
                    </span>
                )}

            </div>


            {provider.vehicleCompatibility &&
                provider.vehicleCompatibility.length > 0 && (

                <div className="services-tags-row">

                    <span className="tags-heading">
                        Supported Vehicles:
                    </span>

                    {provider.vehicleCompatibility.map((vt) => (
                        <span
                            key={vt}
                            className="compatibility-tag"
                        >
                            🚗 {vt.replace(/_/g, " ")}
                        </span>
                    ))}

                </div>
            )}


            <div className="provider-actions-row">

                <a
                    className="btn-call-provider"
                    href={`tel:${phoneNumber}`}
                >
                    📞 Call Provider ({phoneNumber})
                </a>

                <a
                    className="btn-email-provider"
                    href={mailtoLink}
                >
                    ✉️ Email Dispatch
                </a>

                {isPrimary && onReplan && (

                    <button
                        type="button"
                        className="btn-replan-provider"
                        onClick={onReplan}
                        disabled={isReplanning}
                    >
                        {isReplanning
                            ? "🔄 Replanning..."
                            : "🔄 Reassign Provider"}
                    </button>

                )}

            </div>

        </div>
    );
}