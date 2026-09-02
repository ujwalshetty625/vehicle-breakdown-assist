
from pathlib import Path
import re, shutil, sys

ROOT = Path.cwd()
B = ROOT / "backend"
F = ROOT / "frontend"

FILES = [
    B/"app/db/models.py", B/"app/db/seed.py",
    B/"app/schemas/provider.py", B/"app/schemas/match.py",
    B/"app/api/providers.py", B/"app/api/match_provider.py",
    B/"app/api/replan.py", B/"app/api/assist.py",
    F/"src/types/vehicle.ts", F/"src/api/api.ts",
    F/"src/components/ProviderCard.tsx", F/"src/pages/Results.tsx",
]
missing = [str(p) for p in FILES if not p.exists()]
if missing:
    print("Run this from the vehicle-breakdown-assist repository root.")
    print("\n".join(missing))
    sys.exit(1)

def edit(path, fn):
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        shutil.copy2(path, bak)
    old = path.read_text(encoding="utf-8")
    new = fn(old)
    if new != old:
        path.write_text(new, encoding="utf-8")
        print("UPDATED", path)
    else:
        print("OK/SKIP", path)

# 1. Provider DB fields
def models(s):
    if "phone = Column(String" not in s:
        s = s.replace(
            "    name = Column(String, nullable=False)\n",
            "    name = Column(String, nullable=False)\n"
            "    phone = Column(String, nullable=True)\n"
            "    email = Column(String, nullable=True)\n", 1)
    return s
edit(B/"app/db/models.py", models)

# 2. Pydantic schemas
def provider_schema(s):
    if "phone: str | None" not in s:
        s = s.replace(
            "    name: str\n",
            "    name: str\n    phone: str | None = None\n    email: str | None = None\n", 1)
    return s
edit(B/"app/schemas/provider.py", provider_schema)

def match_schema(s):
    if "from pydantic import BaseModel, Field" not in s:
        s = s.replace("from pydantic import BaseModel",
                      "from pydantic import BaseModel, Field")
    if "phone: str | None" not in s:
        s = s.replace(
            "    name: str\n",
            "    name: str\n    phone: str | None = None\n    email: str | None = None\n", 1)
    s = s.replace("    capabilities: list[str] = []",
                  "    capabilities: list[str] = Field(default_factory=list)")
    s = s.replace("    vehicle_types: list[str] = []",
                  "    vehicle_types: list[str] = Field(default_factory=list)")
    return s
edit(B/"app/schemas/match.py", match_schema)

# 3. Backend responses
def providers_api(s):
    if "phone=p.phone" not in s:
        s = s.replace(
            "                name=p.name,\n",
            "                name=p.name,\n                phone=p.phone,\n                email=p.email,\n", 1)
    return s
edit(B/"app/api/providers.py", providers_api)

def match_api(s):
    if "phone=p.phone" not in s:
        s = s.replace(
            "            name=p.name,\n",
            "            name=p.name,\n            phone=p.phone,\n            email=p.email,\n", 1)
    return s
edit(B/"app/api/match_provider.py", match_api)

def replan_api(s):
    if "phone=p.phone" not in s:
        s = s.replace(
            "            name=p.name,\n",
            "            name=p.name,\n            phone=p.phone,\n            email=p.email,\n", 1)
    return s
edit(B/"app/api/replan.py", replan_api)

def assist_api(s):
    if "phone=provider.phone" not in s:
        s = s.replace(
            "            name=provider.name,\n",
            "            name=provider.name,\n            phone=provider.phone,\n            email=provider.email,\n", 1)
    return s
edit(B/"app/api/assist.py", assist_api)

# 4. Seed contact data
CONTACTS = {
    "RESCUE Roadside Assistance": ("+919986500500", "support@rescue-roadside.example"),
    "Star Car Towing Service Bangalore": ("+919845938786", "support@star-car-towing.example"),
    "On Time Assist Towing Service": ("+919177693035", "support@ontime-towing.example"),
    "Shivaraj Towing Service": ("+918496801218", "support@shivaraj-towing.example"),
    "Express Car Service": ("+919844072890", "support@express-car-service.example"),
    "Gundappa Car Care": (None, "support@gundappa-car-care.example"),
    "GoMechanic - Bangalore (HQ)": ("+918398970970", "support@gomechanic-bangalore.example"),
    "R.K. Puncture Shop 24/7": (None, "support@rk-puncture.example"),
    "AYS Tyre Puncture Shop Koramangala": (None, "support@ays-tyre.example"),
    "Puncture Shop Bharath Tyres": (None, "support@bharath-tyres.example"),
    "Roadside Assistance M.A Car Jumpstart Service": (None, "support@ma-jumpstart.example"),
    "RAPID Roadside Assistance 24/7": (None, "support@rapid-roadside.example"),
}

def seed_contacts(s):
    for name, (phone, email) in CONTACTS.items():
        marker = f'"name": "{name}"'
        pos = s.find(marker)
        if pos < 0:
            continue
        end = s.find("\n},", pos)
        if end < 0:
            continue
        block = s[pos:end]
        if '"phone":' in block:
            continue
        rating = re.search(r'"rating":\s*[0-9.]+,\n', block)
        if rating:
            insert_at = pos + rating.end()
            value = "None" if phone is None else repr(phone)
            s = s[:insert_at] + f'"phone": {value},\n"email": {email!r},\n' + s[insert_at:]
    if 'phone=p.get("phone")' not in s:
        s = s.replace(
            '        rating=p["rating"],\n',
            '        rating=p["rating"],\n        phone=p.get("phone"),\n        email=p.get("email"),\n', 1)
    return s
edit(B/"app/db/seed.py", seed_contacts)

# 5. Frontend types
def types(s):
    if "phone?: string | null;" not in s:
        s = s.replace(
            "    name: string;\n\n    latitude: number;",
            "    name: string;\n    phone?: string | null;\n    email?: string | null;\n\n    latitude: number;", 1)
    if "phone?: string | null;" not in s:
        s = s.replace(
            "    name: string;\n    distance_km:",
            "    name: string;\n    phone?: string | null;\n    email?: string | null;\n    distance_km:", 1)
    start = s.find("export interface BackendProvider")
    if start >= 0 and s[start:].count("phone?: string | null;") == 0:
        tail = s[start:]
        tail = tail.replace(
            "    name: string;\n",
            "    name: string;\n    phone?: string | null;\n    email?: string | null;\n", 1)
        s = s[:start] + tail
    return s
edit(F/"src/types/vehicle.ts", types)

# 6. Frontend provider mapping
def api_ts(s):
    if "phone: provider.phone" not in s:
        s = s.replace(
            "        name: provider.name,\n",
            "        name: provider.name,\n        phone: provider.phone ?? null,\n        email: provider.email ?? null,\n", 1)
    return s
edit(F/"src/api/api.ts", api_ts)

# 7. Provider card with real tel/mailto actions
CARD = r'''import type { Provider } from "../types/vehicle";

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
'''
edit(F/"src/components/ProviderCard.tsx", lambda _: CARD)

# 8. Results: fix false provider + fake success message
def results(s):
    s = re.sub(r'\n\s*const \[requestSuccess, setRequestSuccess\] = useState<string \| null>\(null\);\n', "\n", s, count=1)
    s = re.sub(r'\n\s*const handleCallProvider = \(pName: string\) => \{.*?\n\s*\};\n', "\n", s, flags=re.S, count=1)
    s = re.sub(r'\n\s*\{requestSuccess && \(.*?\n\s*\)\}\n', "\n", s, flags=re.S, count=1)

    old = '''    const primaryProvider =
        uniqueProviders.find((p) => p.id === assignedProvider?.id) ||
        (uniqueProviders.length > 0 ? uniqueProviders[0] : null);

    const alternativeProviders = uniqueProviders.filter(p => p.id !== primaryProvider?.id);'''
    new = '''    const assignedFromList = assignedProvider
        ? uniqueProviders.find((p) => p.id === assignedProvider.id)
        : null;

    const primaryProvider = assignedFromList || (
        assignedProvider ? {
            id: assignedProvider.id,
            name: assignedProvider.name,
            latitude: assignedProvider.latitude ?? userLat,
            longitude: assignedProvider.longitude ?? userLng,
            distanceKm: assignedProvider.distance_km,
            etaMinutes: Math.max(5, Math.round(assignedProvider.distance_km * 2.5)),
            rating: assignedProvider.rating,
            available: true,
            services: assignedProvider.capabilities ?? [],
            vehicleCompatibility: assignedProvider.vehicle_types ?? [],
            matchScore: assignedProvider.score,
            phone: assignedProvider.phone ?? null,
            email: assignedProvider.email ?? null,
        } : null
    );

    const alternativeProviders = uniqueProviders.filter(p => p.id !== primaryProvider?.id);'''
    if old in s:
        s = s.replace(old, new, 1)

    s = s.replace(
        '''    const faultName = diagnosis?.fault && diagnosis.fault !== "No Fault"
        ? diagnosis.fault
        : "Engine Misfire / Rich Fuel Ratio";''',
        '''    const faultName = diagnosis?.fault || "Diagnosis unavailable";'''
    )

    s = s.replace("                                onCall={handleCallProvider}\n", "", 1)
    s = s.replace(
        '''                                isReplanning={isReplanning}
                            />''',
        '''                                isReplanning={isReplanning}
                                emailContext={{
                                    vehicleType: diagnosis?.requiredCapability || undefined,
                                    fault: diagnosis?.fault || undefined,
                                    severity: diagnosis?.severity || undefined,
                                    location: userLocationName,
                                }}
                            />''', 1)

    s = s.replace("                                            onCall={handleCallProvider}\n", "", 1)
    s = s.replace(
        '''                                            isPrimary={false}
                                        />''',
        '''                                            isPrimary={false}
                                            emailContext={{
                                                vehicleType: diagnosis?.requiredCapability || undefined,
                                                fault: diagnosis?.fault || undefined,
                                                severity: diagnosis?.severity || undefined,
                                                location: userLocationName,
                                            }}
                                        />''', 1)
    return s
edit(F/"src/pages/Results.tsx", results)

# 9. Small CSS addition
css = F/"src/App.css"
if css.exists():
    def css_edit(s):
        if ".btn-email-provider" not in s:
            s += '''
.btn-email-provider {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    text-decoration: none;
    cursor: pointer;
}
.status-unavailable { opacity: 0.8; }
'''
        return s
    edit(css, css_edit)

# 10. Non-destructive DB migration + contact backfill.
# This uses the project's own SQLAlchemy environment and does NOT drop tables.
try:
    sys.path.insert(0, str(B))
    from sqlalchemy import inspect, text
    from app.db.session import engine, SessionLocal
    from app.db.models import Provider

    tables = inspect(engine).get_table_names()
    if "providers" in tables:
        cols = {c["name"] for c in inspect(engine).get_columns("providers")}
        with engine.begin() as conn:
            if "phone" not in cols:
                conn.execute(text("ALTER TABLE providers ADD COLUMN phone VARCHAR"))
                print("DB: added providers.phone")
            if "email" not in cols:
                conn.execute(text("ALTER TABLE providers ADD COLUMN email VARCHAR"))
                print("DB: added providers.email")

        db = SessionLocal()
        try:
            for name, (phone, email) in CONTACTS.items():
                p = db.query(Provider).filter(Provider.name == name).first()
                if p:
                    p.phone = phone
                    p.email = email
            db.commit()
            print("DB: provider contacts backfilled")
        finally:
            db.close()
    else:
        print("DB: providers table not present; seed normally will create it.")
except Exception as exc:
    print("DB migration skipped:", exc)
    print("If needed, run `python -m app.db.seed` from backend after reviewing the seed data.")

print("\nPATCH COMPLETE")
print("Backups: *.bak")
print("Next:")
print("  cd backend")
print("  python -m pytest tests/ -v")
print("Then restart uvicorn and Vite.")
