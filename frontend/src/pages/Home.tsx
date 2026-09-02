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
                        <span className="logo-subtitle">Breakdown Assist</span>
                    </div>
                </div>

                <div className="nav-actions">
                    <span className="status-badge">
                        <span className="pulse-dot green-dot" /> 24/7 Active Dispatch
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
                        Next-Gen Vehicle Breakdown & Diagnostics
                    </div>

                    <h1>
                        Instant AI Diagnosis &
                        <br />
                        <span className="gradient-text">Roadside Assistance Dispatch</span>
                    </h1>

                    <p>
                        Stuck on the road? RoadGuard AI auto-scans vehicle telemetry, accurately predicts faults using trained machine learning models, and dispatches the nearest compatible mechanic or towing service across Bengaluru.
                    </p>

                    <div className="hero-cta-group">
                        <button className="primary-button hero-cta-btn" onClick={onReport}>
                            <span>Report Breakdown Now</span>
                            <ArrowRight size={20} />
                        </button>
                        <span className="cta-subtext">⚡ 1-Click Automated OBD-II ECU Telemetry Fetching</span>
                    </div>
                </div>

                <div className="hero-card glass-card">
                    <div className="card-icon-wrapper">
                        <Wrench size={36} />
                    </div>

                    <h3>Smart Recovery Engine</h3>

                    <p className="pipeline-steps">
                        Telematics → ML Fault Engine → Capability Matching → Dispatch
                    </p>

                    <div className="stats-row">
                        <div className="stat-item">
                            <span className="stat-number">19</span>
                            <span className="stat-label">Vehicle Types</span>
                        </div>
                        <div className="stat-divider" />
                        <div className="stat-item">
                            <span className="stat-number">12+</span>
                            <span className="stat-label">Providers</span>
                        </div>
                        <div className="stat-divider" />
                        <div className="stat-item">
                            <span className="stat-number">&lt; 15m</span>
                            <span className="stat-label">Avg Arrival</span>
                        </div>
                    </div>

                    <div className="system-ready-indicator">
                        <span className="status-dot green-dot" />
                        Backend DB & ML Engine Connected
                    </div>
                </div>
            </main>

            <section className="features-grid">
                <div className="feature-card glass-card">
                    <div className="feature-icon cyan-icon">
                        <Zap size={28} />
                    </div>
                    <h3>Automated Telemetry Fetching</h3>
                    <p>
                        No manual data entry required. Automatically fetch diagnostic telemetry (RPM, AFR, MAP, emissions) directly from backend vehicle databases.
                    </p>
                </div>

                <div className="feature-card glass-card">
                    <div className="feature-icon green-icon">
                        <Car size={28} />
                    </div>
                    <h3>All 19 Vehicle Types Supported</h3>
                    <p>
                        From motorcycles, scooters, auto-rickshaws, and passenger sedans to commercial heavy trucks, buses, and tractors.
                    </p>
                </div>

                <div className="feature-card glass-card">
                    <div className="feature-icon orange-icon">
                        <MapPin size={28} />
                    </div>
                    <h3>Instant Replan & Dispatch</h3>
                    <p>
                        Automated distance-based provider matching in Bengaluru with instant re-assignment capabilities if primary providers are occupied.
                    </p>
                </div>
            </section>
        </div>
    );
}

export default Home;