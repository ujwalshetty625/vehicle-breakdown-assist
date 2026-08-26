import { Activity, ArrowRight, ShieldCheck, Wrench } from "lucide-react";

function Home({ onReport }: { onReport: () => void }) {
    return (
        <div className="home-page">
            <nav className="navbar">
                <div className="logo">
                    <Activity size={28} />
                    <span>RoadGuard AI</span>
                </div>

                <button className="nav-button" onClick={onReport}>
                    Report Breakdown
                </button>
            </nav>

            <main className="hero">
                <div className="hero-content">
                    <div className="badge">
                        <ShieldCheck size={16} />
                        Intelligent Roadside Recovery
                    </div>

                    <h1>
                        Smarter Help When
                        <br />
                        Your Vehicle Breaks Down
                    </h1>

                    <p>
                        RoadGuard AI analyzes your vehicle breakdown, estimates the
                        possible fault, determines the assistance required, and helps
                        find the most suitable roadside service.
                    </p>

                    <button className="primary-button" onClick={onReport}>
                        Report a Breakdown
                        <ArrowRight size={20} />
                    </button>
                </div>

                <div className="hero-card">
                    <div className="card-icon">
                        <Wrench size={32} />
                    </div>

                    <h3>Intelligent Recovery</h3>

                    <p>
                        Predict → Diagnose → Assist → Recover
                    </p>

                    <div className="status">
                        <span className="status-dot"></span>
                        System Ready
                    </div>
                </div>
            </main>

            <section className="features">
                <div className="feature-card">
                    <Activity size={24} />
                    <h3>AI Diagnosis</h3>
                    <p>
                        Estimate possible vehicle faults and communicate confidence.
                    </p>
                </div>

                <div className="feature-card">
                    <ShieldCheck size={24} />
                    <h3>Safety First</h3>
                    <p>
                        Consider breakdown severity and roadside safety conditions.
                    </p>
                </div>

                <div className="feature-card">
                    <Wrench size={24} />
                    <h3>Smart Assistance</h3>
                    <p>
                        Match the breakdown with the appropriate roadside assistance.
                    </p>
                </div>
            </section>
        </div>
    );
}

export default Home;