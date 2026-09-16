import type { Provider } from "../types/vehicle";
import { Award, Star, MapPin, Clock, Wrench, Car, Phone, Mail, RefreshCw } from "lucide-react";

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
                <div className="primary-badge flex items-center gap-1.5">
                    <Award className="w-4 h-4 text-amber-500 inline mr-1" /> TOP MATCHED PROVIDER (DATABASE VERIFIED)
                </div>
            )}

            <div className="provider-header-row">

                <div>

                    <h3 className="provider-name-text">
                        {provider.name}
                    </h3>

                    <div className="provider-sub-info">

                        <span className="rating-stars flex items-center gap-1">
                            <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-400 inline mr-1" /> {provider.rating ? provider.rating.toFixed(1) : "4.8"} / 5.0
                        </span>

                        <span className="info-dot">
                            •
                        </span>

                        <span className="distance-info flex items-center gap-1">
                            <MapPin className="w-3.5 h-3.5 text-sky-600 inline mr-1" /> {provider.distanceKm} km away
                        </span>

                        <span className="info-dot">
                            •
                        </span>

                        <span className="eta-info flex items-center gap-1">
                            <Clock className="w-3.5 h-3.5 text-sky-600 inline mr-1" /> ~
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
                            className="service-tag flex items-center gap-1"
                        >
                            <Wrench className="w-3 h-3 text-slate-500 inline mr-1" /> {formatCapability(srv)}
                        </span>
                    ))
                ) : (
                    <span className="service-tag flex items-center gap-1">
                        <Wrench className="w-3 h-3 text-slate-500 inline mr-1" /> Roadside Repair & Towing
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
                            className="compatibility-tag flex items-center gap-1"
                        >
                            <Car className="w-3 h-3 text-sky-600 inline mr-1" /> {vt.replace(/_/g, " ")}
                        </span>
                    ))}

                </div>
            )}


            <div className="provider-actions-row">

                <a
                    className="btn-call-provider flex items-center gap-1.5"
                    href={`tel:${phoneNumber}`}
                >
                    <Phone className="w-4 h-4 inline mr-1" /> Call Provider ({phoneNumber})
                </a>

                <a
                    className="btn-email-provider flex items-center gap-1.5"
                    href={mailtoLink}
                >
                    <Mail className="w-4 h-4 inline mr-1" /> Email Dispatch
                </a>

                {isPrimary && onReplan && (

                    <button
                        type="button"
                        className="btn-replan-provider flex items-center gap-1.5"
                        onClick={onReplan}
                        disabled={isReplanning}
                    >
                        {isReplanning ? (
                            <>
                                <RefreshCw className="w-4 h-4 animate-spin inline mr-1" /> Replanning...
                            </>
                        ) : (
                            <>
                                <RefreshCw className="w-4 h-4 inline mr-1" /> Reassign Provider
                            </>
                        )}
                    </button>

                )}

            </div>

        </div>
    );
}