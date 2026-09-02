import { Activity, ArrowRight, ShieldCheck, Wrench, Car, Zap, MapPin } from "lucide-react";

function Home({ onReport }: { onReport: () => void }) {
    return (
        <div className="home-page">
            <nav className="navbar glass-card">
                <div className="logo">
                    <div className="logo-icon">
                        <Activity size={26} />
                    </div>
                    <div className="logo-text">
                        <span className="logo-title">RoadGuard AI</span>
                        <span className="logo-subtitle">24/7 Breakdown Assist</span>
                    </div>
                </div>

                <div className="nav-actions">
                    <span className="status-badge">
                        <span className="pulse-dot green-dot" /> Instant Assistance Active
                    </span>
                    <button className="nav-button glow-btn" onClick={onReport}>
                        🚨 Emergency Assist
                    </button>
                </div>
            </nav>

            <main className="hero">
                <div className="hero-content">
                    <div className="badge-pill hero-badge">
                        <ShieldCheck size={16} />
                        24/7 Intelligent Roadside Assistance & Recovery
                    </div>

                    <h1>
                        Stuck on the Road?
                        <br />
                        <span className="gradient-text">Instant Diagnostics & Help Dispatch</span>
                    </h1>

                    <p>
                        Fast, reliable assistance whenever you experience a vehicle breakdown. Auto-scans vehicle telemetry, identifies breakdown causes, assesses safety risks, and dispatches certified nearby mechanics and towing services across Bengaluru.
                    </p>

                    <div className="hero-cta-group">
                        <button className="primary-button hero-cta-btn" onClick={onReport}>
                            <span>🚨 Request Emergency Assistance</span>
                            <ArrowRight size={20} />
                        </button>
                        <span className="cta-subtext">⚡ 1-Click Diagnostics & Verified Provider Matching</span>
                    </div>
                </div>

                <div className="hero-card glass-card">
                    <div className="card-icon-wrapper">
                        <Wrench size={36} />
                    </div>

                    <h3>Smart Emergency Dispatch Pipeline</h3>

                    <p className="pipeline-steps">
                        Diagnostic Scan → Fault Analysis → Safety Assessment → Instant Mechanic Dispatch
                    </p>

                    <div className="stats-row">
                        <div className="stat-item">
                            <span className="stat-number">24/7</span>
                            <span className="stat-label">Roadside Support</span>
                        </div>
                        <div className="stat-divider" />
                        <div className="stat-item">
                            <span className="stat-number">Smart</span>
                            <span className="stat-label">Fault Matching</span>
                        </div>
                        <div className="stat-divider" />
                        <div className="stat-item">
                            <span className="stat-number">GPS</span>
                            <span className="stat-label">Nearby Dispatch</span>
                        </div>
                    </div>

                    <div className="system-ready-indicator">
                        <span className="status-dot green-dot" />
                        24/7 Roadside Assistance Network Ready
                    </div>
                </div>
            </main>

            <section className="features-grid">
                <div className="feature-card glass-card">
                    <div className="feature-icon cyan-icon">
                        <Zap size={28} />
                    </div>
                    <h3>Instant Breakdown Diagnostics</h3>
                    <p>
                        Analyzes vehicle sensors, dashboard warning light photos, and symptoms to pinpoint the exact breakdown cause in seconds.
                    </p>
                </div>

                <div className="feature-card glass-card">
                    <div className="feature-icon green-icon">
                        <Car size={28} />
                    </div>
                    <h3>Safety Protocol & Guidance</h3>
                    <p>
                        Provides immediate driveability assessments (Safe to Drive vs Pull Over), severity risk ratings, and clear roadside waiting guidance.
                    </p>
                </div>

                <div className="feature-card glass-card">
                    <div className="feature-icon orange-icon">
                        <MapPin size={28} />
                    </div>
                    <h3>Verified Nearby Mechanics</h3>
                    <p>
                        Matches certified local providers in Bengaluru based on your vehicle's exact requirements (Battery Jumpstart, Towing, Tire Change, Engine Repair).
                    </p>
                </div>
            </section>
        </div>
    );
}

export default Home;