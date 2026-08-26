import {
    ArrowLeft,
    CheckCircle,
    Clock,
    MapPin,
    ShieldAlert,
    Star,
    Wrench,
} from "lucide-react";

import type { Provider } from "../types/vehicle";

interface ResultsProps {
    onBack: () => void;
    providers?: Provider[];
}

function Results({
    onBack,
    providers = [],
}: ResultsProps) {

    const recommendedProvider = providers[0];
    const alternativeProviders = providers.slice(1);

    return (
        <div className="results-page">

            {/* =====================================================
                HEADER
            ===================================================== */}

            <header className="results-header">

                <button
                    className="back-button"
                    onClick={onBack}
                >
                    <ArrowLeft size={20} />
                    Back
                </button>

                <div className="results-title">
                    <Wrench size={24} />
                    <span>Breakdown Assessment</span>
                </div>

            </header>


            {/* =====================================================
                MAIN
            ===================================================== */}

            <main className="results-container">


                {/* =================================================
                    INTRO
                ================================================= */}

                <div className="results-intro">

                    <div>

                        <p className="small-label">
                            ASSESSMENT COMPLETE
                        </p>

                        <h1>
                            Your Breakdown Assessment
                        </h1>

                        <p>
                            Our system has analyzed the information you
                            provided and identified the most likely
                            breakdown category.
                        </p>

                    </div>


                    <div className="complete-badge">

                        <CheckCircle size={18} />

                        Analysis Complete

                    </div>

                </div>


                {/* =================================================
                    DIAGNOSIS
                ================================================= */}

                <section className="result-card diagnosis-result">

                    <div className="card-heading">

                        <div className="result-icon">
                            <Wrench size={24} />
                        </div>

                        <div>

                            <p className="card-label">
                                POSSIBLE FAULT
                            </p>

                            <h2>
                                Battery / Electrical Failure
                            </h2>

                        </div>

                    </div>


                    {/* Confidence */}

                    <div className="confidence-section">

                        <div className="confidence-header">

                            <span>
                                AI Confidence
                            </span>

                            <strong>
                                82%
                            </strong>

                        </div>


                        <div className="confidence-bar">

                            <div
                                className="confidence-fill"
                                style={{
                                    width: "82%",
                                }}
                            />

                        </div>


                        <p>
                            The system estimates that a battery or
                            electrical issue is the most likely cause
                            based on the available information.
                        </p>

                    </div>

                </section>


                {/* =================================================
                    SEVERITY + SAFETY
                ================================================= */}

                <div className="result-grid">


                    {/* Severity */}

                    <section className="result-card severity-card">

                        <div className="card-heading">

                            <div className="severity-icon">
                                <ShieldAlert size={24} />
                            </div>

                            <div>

                                <p className="card-label">
                                    SEVERITY
                                </p>

                                <h2>
                                    High
                                </h2>

                            </div>

                        </div>


                        <p>
                            The vehicle may require roadside assistance
                            and should not be driven until the issue
                            is assessed.
                        </p>

                    </section>


                    {/* Safety */}

                    <section className="result-card safety-card">

                        <div className="card-heading">

                            <div className="safety-icon">
                                <ShieldAlert size={24} />
                            </div>

                            <div>

                                <p className="card-label">
                                    SAFETY RECOMMENDATION
                                </p>

                                <h2>
                                    Stay Safe
                                </h2>

                            </div>

                        </div>


                        <p>
                            Move to a safe location if possible and
                            avoid continuing to drive the vehicle.
                        </p>

                    </section>

                </div>


                {/* =================================================
                    ASSISTANCE REQUIRED
                ================================================= */}

                <section className="result-card">

                    <p className="card-label">
                        RECOMMENDED ASSISTANCE
                    </p>


                    <div className="assistance-row">

                        <div className="assistance-icon">
                            <Wrench size={25} />
                        </div>


                        <div>

                            <h2>
                                Battery / Electrical Technician
                            </h2>

                            <p>
                                A technician equipped to handle battery
                                and electrical problems is recommended.
                            </p>

                        </div>

                    </div>

                </section>


                {/* =================================================
                    PROVIDER LOCATION
                ================================================= */}

                <section className="provider-location-section">

                    <div className="section-heading">

                        <div>

                            <p className="small-label">
                                PROVIDER LOCATION
                            </p>

                            <h2>
                                Nearby Assistance
                            </h2>

                        </div>

                    </div>


                    <div className="provider-map">


                        {/* USER LOCATION */}

                        <div className="map-user-location">

                            <MapPin size={22} />

                            <span>
                                Your Location
                            </span>

                        </div>


                        {/* PROVIDERS */}

                        {providers.map((provider) => (

                            <div
                                key={provider.id}
                                className={`map-provider provider-${provider.id}`}
                            >

                                <div className="map-provider-dot" />

                                <div className="map-provider-info">

                                    <strong>
                                        {provider.name}
                                    </strong>

                                    <span>
                                        {provider.distanceKm} km
                                        {" • "}
                                        {provider.etaMinutes} min
                                    </span>

                                </div>

                            </div>

                        ))}


                        {/* NO PROVIDERS */}

                        {providers.length === 0 && (

                            <div className="map-no-providers">

                                <MapPin size={26} />

                                <span>
                                    No nearby providers available
                                </span>

                            </div>

                        )}

                    </div>

                </section>


                {/* =================================================
                    SMART PROVIDER MATCH
                ================================================= */}

                <section className="provider-section">

                    <div className="section-heading">

                        <div>

                            <p className="small-label">
                                SMART PROVIDER MATCH
                            </p>

                            <h2>
                                Recommended Assistance Provider
                            </h2>

                        </div>


                        {recommendedProvider && (

                            <span className="recommended-badge">
                                Best Match
                            </span>

                        )}

                    </div>


                    {/* =================================================
                        NO PROVIDERS
                    ================================================= */}

                    {!recommendedProvider && (

                        <div className="result-card no-provider-card">

                            <MapPin size={30} />

                            <h3>
                                No providers found
                            </h3>

                            <p>
                                We couldn't find a suitable assistance
                                provider near your current location.
                            </p>

                        </div>

                    )}


                    {/* =================================================
                        RECOMMENDED PROVIDER
                    ================================================= */}

                    {recommendedProvider && (

                        <div className="provider-card">


                            {/* Provider Header */}

                            <div className="provider-main">

                                <div className="provider-avatar">

                                    {recommendedProvider.name
                                        .substring(0, 2)
                                        .toUpperCase()}

                                </div>


                                <div>

                                    <h3>
                                        {recommendedProvider.name}
                                    </h3>


                                    <div className="provider-rating">

                                        <Star
                                            size={16}
                                            fill="currentColor"
                                        />

                                        <span>
                                            {recommendedProvider.rating}
                                        </span>

                                        <span>
                                            •
                                        </span>

                                        <span>
                                            {recommendedProvider.available
                                                ? "Available now"
                                                : "Currently unavailable"}
                                        </span>

                                    </div>

                                </div>

                            </div>


                            {/* Provider Details */}

                            <div className="provider-details">

                                <div>

                                    <MapPin size={18} />

                                    <span>
                                        {recommendedProvider.distanceKm}
                                        {" km away"}
                                    </span>

                                </div>


                                <div>

                                    <Clock size={18} />

                                    <span>
                                        ETA:{" "}
                                        {recommendedProvider.etaMinutes}
                                        {" minutes"}
                                    </span>

                                </div>

                            </div>


                            {/* Services */}

                            <div className="provider-services">

                                {recommendedProvider.services.map(
                                    (service) => (

                                        <span
                                            key={service}
                                            className="service-tag"
                                        >
                                            {service}
                                        </span>

                                    )
                                )}

                            </div>


                            {/* Request Assistance */}

                            <button
                                className="request-button"
                                onClick={() => {
                                    alert(
                                        `Assistance requested from ${recommendedProvider.name}`
                                    );
                                }}
                            >
                                Request Assistance
                            </button>

                        </div>

                    )}


                    {/* =================================================
                        ALTERNATIVE PROVIDERS
                    ================================================= */}

                    {alternativeProviders.length > 0 && (

                        <div className="alternative-section">

                            <h3>
                                Alternative Providers
                            </h3>


                            {alternativeProviders.map(
                                (provider) => (

                                    <div
                                        className="alternative-card"
                                        key={provider.id}
                                    >

                                        <div>

                                            <strong>
                                                {provider.name}
                                            </strong>


                                            <p>

                                                {provider.distanceKm}
                                                {" km"}
                                                {" • "}
                                                ETA{" "}
                                                {provider.etaMinutes}
                                                {" min"}
                                                {" • "}
                                                {provider.available
                                                    ? "Available"
                                                    : "Unavailable"}

                                            </p>

                                        </div>


                                        <button
                                            className="secondary-button"
                                            onClick={() => {
                                                alert(
                                                    `Selected ${provider.name}`
                                                );
                                            }}
                                        >
                                            Select
                                        </button>

                                    </div>

                                )
                            )}

                        </div>

                    )}

                </section>

            </main>

        </div>
    );
}

export default Results;