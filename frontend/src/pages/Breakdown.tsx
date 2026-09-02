import { useState, useEffect, useRef } from "react";
import type { FormEvent, ChangeEvent } from "react";
import type {
    BreakdownData,
    VehicleType,
    DiagnosisResult,
    DiagnosticPreset,
    VehicleCategoryGroup,
} from "../types/vehicle";
import { getVehicleTypes, getDiagnosticPresets, autoScanVehicleECU } from "../api/api";

interface BreakdownProps {
    onBack: () => void;
    onComplete: (data: BreakdownData, result?: DiagnosisResult) => void;
}

// Popular Vehicle Brands for quick 1-click selection
const QUICK_BRANDS = [
    { name: "Honda", icon: "🚗", model: "Honda City" },
    { name: "Hyundai", icon: "🚘", model: "Hyundai Creta" },
    { name: "Maruti Suzuki", icon: "🚗", model: "Maruti Swift" },
    { name: "Tata", icon: "🚙", model: "Tata Nexon" },
    { name: "Mahindra", icon: "🚙", model: "Mahindra Thar" },
    { name: "Royal Enfield", icon: "🏍️", model: "Classic 350" },
    { name: "TVS", icon: "🛵", model: "TVS Jupiter" },
    { name: "Toyota", icon: "🚘", model: "Toyota Fortuner" },
];

// Interactive Breakdown Symptom Cards
const QUICK_SYMPTOMS = [
    {
        id: "symptom_smoke",
        title: "Heavy Exhaust Smoke & Power Loss",
        icon: "💨",
        symptomText: "Heavy dark exhaust smoke, engine misfire, sputtering sound and severe power loss while accelerating.",
        warning: "Check Engine / Malfunction Indicator",
        presetId: "preset_rich_mixture"
    },
    {
        id: "symptom_battery",
        title: "Battery Dead & Engine Click",
        icon: "⚡",
        symptomText: "Engine won't turn over, rapid clicking sound when turning ignition, dim dashboard and headlights.",
        warning: "Battery / Alternator Symbol",
        presetId: "preset_low_voltage"
    },
    {
        id: "symptom_hesitation",
        title: "Engine Hesitation & Surging",
        icon: "🌡️",
        symptomText: "Vehicle hesitates under load, popping intake noise, unstable RPM idle and vacuum leak symptoms.",
        warning: "Air/Fuel Fault / Service Engine",
        presetId: "preset_lean_mixture"
    },
    {
        id: "symptom_tire",
        title: "Flat Tire or Wheel Puncture",
        icon: "🛑",
        symptomText: "Flat tire on roadside, loss of tire pressure, wheel vibrating.",
        warning: "TPMS Low Pressure Light",
        presetId: "preset_tire_damage"
    }
];

// Preset Bengaluru Landmark Locations for instant selection
const BENGALURU_PRESETS = [
    { name: "Koramangala, 5th Block", lat: 12.9345, lng: 77.6265 },
    { name: "Indiranagar, 100ft Road", lat: 12.9784, lng: 77.6408 },
    { name: "MG Road Metro Station", lat: 12.9756, lng: 77.6066 },
    { name: "Whitefield Tech Park", lat: 12.9698, lng: 77.7499 },
    { name: "Electronic City Phase 1", lat: 12.8452, lng: 77.6602 },
    { name: "Hebbal Flyover", lat: 13.0358, lng: 77.5970 },
];

function Breakdown({ onBack, onComplete }: BreakdownProps) {
    /* Vehicle information state */
    const [vehicleModel, setVehicleModel] = useState("");
    const [vehicleYear, setVehicleYear] = useState("");
    const [vehicleType, setVehicleType] = useState<VehicleType>("car");
    const [fuelType, setFuelType] = useState("Petrol");

    /* Vehicle Categories */
    const [vehicleCategories, setVehicleCategories] = useState<VehicleCategoryGroup[]>([]);

    /* Breakdown details */
    const [symptoms, setSymptoms] = useState("");
    const [warningLight, setWarningLight] = useState("");
    const [location, setLocation] = useState("");
    const [latitude, setLatitude] = useState<number | null>(null);
    const [longitude, setLongitude] = useState<number | null>(null);

    /* Engine / Breakdown Photo Upload & Camera state */
    const [enginePhoto, setEnginePhoto] = useState<string | null>(null);
    const [photoName, setPhotoName] = useState<string>("");
    const fileInputRef = useRef<HTMLInputElement>(null);
    const cameraInputRef = useRef<HTMLInputElement>(null);

    /* Voice Input State */
    const [isListening, setIsListening] = useState(false);
    const recognitionRef = useRef<any>(null);

    /* Diagnostic Telemetry state */
    const [presets, setPresets] = useState<DiagnosticPreset[]>([]);
    const [selectedPresetId, setSelectedPresetId] = useState<string>("preset_rich_mixture");
    const [isScanningECU, setIsScanningECU] = useState(false);
    const [telemetryFetched, setTelemetryFetched] = useState(false);
    const [showFineTune, setShowFineTune] = useState(false);
    const [activeSymptomId, setActiveSymptomId] = useState<string>("");

    /* Voice Speech Recognition Handler */
    const handleToggleVoiceInput = () => {
        const windowObj = window as any;
        const SpeechRecognitionClass = windowObj.SpeechRecognition || windowObj.webkitSpeechRecognition;

        if (!SpeechRecognitionClass) {
            setError("Voice speech recognition is not supported in this browser. Please type symptoms into the text field.");
            return;
        }

        if (isListening) {
            if (recognitionRef.current) {
                recognitionRef.current.stop();
            }
            setIsListening(false);
            setSuccessMsg("⏹️ Voice recording stopped.");
            setTimeout(() => setSuccessMsg(""), 3000);
            return;
        }

        try {
            const recognition = new SpeechRecognitionClass();
            recognitionRef.current = recognition;
            recognition.continuous = false;
            recognition.interimResults = true;
            recognition.lang = "en-US";

            setIsListening(true);
            setError("");
            setSuccessMsg("🎤 Listening... Speak your breakdown symptoms clearly.");

            recognition.onresult = (event: any) => {
                let currentTranscript = "";
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    currentTranscript += event.results[i][0].transcript;
                }
                if (currentTranscript) {
                    setSymptoms(currentTranscript);
                }
            };

            recognition.onerror = (err: any) => {
                console.error("Speech recognition error:", err);
                setIsListening(false);
                setError("Microphone permission denied or speech unrecognized. Try again.");
            };

            recognition.onend = () => {
                setIsListening(false);
            };

            recognition.start();
        } catch (err) {
            console.error("Voice input error:", err);
            setIsListening(false);
            setError("Unable to launch voice microphone recording.");
        }
    };

    /* 14 ML Telemetry fields */
    const [MAP, setMAP] = useState("1.044");
    const [TPS, setTPS] = useState("0.769");
    const [Force, setForce] = useState("80.04");
    const [Power, setPower] = useState("0.497");
    const [RPM, setRPM] = useState("1188.55");
    const [consumptionLh, setConsumptionLh] = useState("1.989");
    const [consumptionL100km, setConsumptionL100km] = useState("8.207");
    const [Speed, setSpeed] = useState("25.038");
    const [CO, setCO] = useState("1.925");
    const [HC, setHC] = useState("247.44");
    const [CO2, setCO2] = useState("12.834");
    const [O2, setO2] = useState("0.56");
    const [Lambda, setLambda] = useState("1.003");
    const [AFR, setAFR] = useState("14.75");

    const [loading, setLoading] = useState(false);
    const [locationLoading, setLocationLoading] = useState(false);
    const [error, setError] = useState("");
    const [successMsg, setSuccessMsg] = useState("");

    // Load backend vehicle types & diagnostic presets
    useEffect(() => {
        const loadInitialBackendData = async () => {
            try {
                const vtData = await getVehicleTypes();
                if (vtData.categories && vtData.categories.length > 0) {
                    setVehicleCategories(vtData.categories);
                }

                const presetsData = await getDiagnosticPresets();
                if (presetsData && presetsData.length > 0) {
                    setPresets(presetsData);
                }
            } catch (err) {
                console.error("Error initializing backend data:", err);
            }
        };

        loadInitialBackendData();
    }, []);

    // Apply preset diagnostic telemetry
    const applyPresetValues = (preset: DiagnosticPreset) => {
        const t = preset.telemetry;
        setMAP(String(t.MAP));
        setTPS(String(t.TPS));
        setForce(String(t.Force));
        setPower(String(t.Power));
        setRPM(String(t.RPM));
        setConsumptionLh(String(t.consumption_lh));
        setConsumptionL100km(String(t.consumption_l100km));
        setSpeed(String(t.Speed));
        setCO(String(t.CO));
        setHC(String(t.HC));
        setCO2(String(t.CO2));
        setO2(String(t.O2));
        setLambda(String(t.Lambda));
        setAFR(String(t.AFR));
        setTelemetryFetched(true);
        setSelectedPresetId(preset.id);
    };

    // Built-in fallback preset telemetry mapping for instantaneous application
    const BUILTIN_PRESETS: Record<string, DiagnosticPreset> = {
        preset_low_voltage: {
            id: "preset_low_voltage",
            name: "Low Battery Voltage / Electrical Fault",
            fault_name: "Low Voltage",
            description: "Battery voltage drop",
            symptoms: "Engine click",
            telemetry: { MAP: 1.685, TPS: 0.983, Force: 283.63, Power: 3.236, RPM: 1878.75, consumption_lh: 3.202, consumption_l100km: 7.952, Speed: 40.384, CO: 0.462, HC: 214.24, CO2: 12.971, O2: 0.87, Lambda: 1.04, AFR: 15.284 }
        },
        preset_rich_mixture: {
            id: "preset_rich_mixture",
            name: "Engine Misfire & Rich Mixture",
            fault_name: "Rich Mixture",
            description: "High CO levels",
            symptoms: "Exhaust smoke",
            telemetry: { MAP: 1.044, TPS: 0.769, Force: 80.04, Power: 0.497, RPM: 1188.55, consumption_lh: 1.989, consumption_l100km: 8.207, Speed: 25.038, CO: 1.925, HC: 247.44, CO2: 12.834, O2: 0.56, Lambda: 1.003, AFR: 14.75 }
        },
        preset_lean_mixture: {
            id: "preset_lean_mixture",
            name: "Lean Mixture / Air Intake Leak",
            fault_name: "Lean Mixture",
            description: "High O2 levels",
            symptoms: "Surging idle",
            telemetry: { MAP: 1.614, TPS: 1.095, Force: 78.864, Power: 1.844, RPM: 3566.67, consumption_lh: 4.489, consumption_l100km: 5.626, Speed: 77.641, CO: 0.722, HC: 148.625, CO2: 14.189, O2: 1.119, Lambda: 1.074, AFR: 15.788 }
        },
        preset_tire_damage: {
            id: "preset_tire_damage",
            name: "Flat Tire / Puncture Damage",
            fault_name: "Flat Tire",
            description: "Puncture",
            symptoms: "Flat tire",
            telemetry: { MAP: 3.549, TPS: 1.889, Force: 7.428, Power: 5.227, RPM: 1192.77, consumption_lh: 3.057, consumption_l100km: 11.72, Speed: 0.0, CO: 0.46, HC: 196.089, CO2: 14.356, O2: 1.08, Lambda: 1.047, AFR: 15.385 }
        }
    };

    // Handle Quick Symptom Click
    const handleQuickSymptomClick = (symptomItem: typeof QUICK_SYMPTOMS[0]) => {
        setActiveSymptomId(symptomItem.id);
        setSymptoms(symptomItem.symptomText);
        setWarningLight(symptomItem.warning);

        const matchedPreset = presets.find((p) => p.id === symptomItem.presetId) || BUILTIN_PRESETS[symptomItem.presetId];
        if (matchedPreset) {
            applyPresetValues(matchedPreset);
            setSuccessMsg(`⚡ Auto-configured OBD-II telemetry profile for "${symptomItem.title}"`);
            setTimeout(() => setSuccessMsg(""), 4000);
        }
    };

    // Handle Quick Brand Select
    const handleQuickBrandClick = (b: typeof QUICK_BRANDS[0]) => {
        setVehicleModel(b.model);
        if (b.name === "Royal Enfield" || b.name === "TVS") {
            setVehicleType("motorcycle");
        } else {
            setVehicleType("car");
        }
    };

    // Handle Image File Upload
    const handleImageUpload = (event: ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        if (file.size > 5 * 1024 * 1024) {
            setError("Image file size should be less than 5MB.");
            return;
        }

        setError("");
        setPhotoName(file.name);

        const reader = new FileReader();
        reader.onloadend = () => {
            setEnginePhoto(reader.result as string);
            setSuccessMsg(`📸 Engine photo attached successfully: ${file.name}`);
            setTimeout(() => setSuccessMsg(""), 4000);
        };
        reader.readAsDataURL(file);
    };

    // Remove Uploaded Image
    const handleRemoveImage = () => {
        setEnginePhoto(null);
        setPhotoName("");
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    // Auto-scan vehicle ECU from backend API
    const handleAutoScanECU = async () => {
        setIsScanningECU(true);
        setError("");
        setSuccessMsg("");

        try {
            const result = await autoScanVehicleECU(vehicleModel || "Vehicle", vehicleType, symptoms);
            if (result && result.telemetry) {
                const t = result.telemetry;
                setMAP(String(t.MAP));
                setTPS(String(t.TPS));
                setForce(String(t.Force));
                setPower(String(t.Power));
                setRPM(String(t.RPM));
                setConsumptionLh(String(t.consumption_lh));
                setConsumptionL100km(String(t.consumption_l100km));
                setSpeed(String(t.Speed));
                setCO(String(t.CO));
                setHC(String(t.HC));
                setCO2(String(t.CO2));
                setO2(String(t.O2));
                setLambda(String(t.Lambda));
                setAFR(String(t.AFR));
                setTelemetryFetched(true);
                setSuccessMsg(`⚡ Live ECU Scan complete! Fetched telemetry for: ${result.matched_preset || 'diagnostic profile'}`);
            }
        } catch (err) {
            setError("ECU Scan connection simulation active. Fetched default diagnostic profile.");
            if (presets.length > 0) {
                applyPresetValues(presets[0]);
            }
        } finally {
            setIsScanningECU(false);
            setTimeout(() => setSuccessMsg(""), 5000);
        }
    };

    /* Select quick location preset */
    const handleSelectPresetLocation = (p: typeof BENGALURU_PRESETS[0]) => {
        setLocation(p.name);
        setLatitude(p.lat);
        setLongitude(p.lng);
    };

    /* Get current GPS location */
    const getCurrentLocation = () => {
        if (!navigator.geolocation) {
            setError("Geolocation is not supported by your browser.");
            return;
        }

        setLocationLoading(true);
        setError("");

        navigator.geolocation.getCurrentPosition(
            (position) => {
                setLatitude(position.coords.latitude);
                setLongitude(position.coords.longitude);
                setLocation(`GPS Location (${position.coords.latitude.toFixed(4)}, ${position.coords.longitude.toFixed(4)})`);
                setLocationLoading(false);
            },
            () => {
                setLocationLoading(false);
                setLatitude(12.9345);
                setLongitude(77.6265);
                setLocation("Koramangala, 5th Block, Bengaluru");
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
        );
    };

    /* Helper conversion */
    const numberVal = (val: string): number => {
        const p = Number(val);
        return Number.isFinite(p) ? p : 0;
    };

    /* Form Submit */
    const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setError("");

        if (!vehicleModel.trim()) {
            setError("Please enter your vehicle brand and model (e.g. Honda City).");
            return;
        }

        if (!symptoms.trim()) {
            setError("Please select or describe the vehicle symptoms.");
            return;
        }

        let telemetryObj = {
            MAP: numberVal(MAP),
            TPS: numberVal(TPS),
            Force: numberVal(Force),
            Power: numberVal(Power),
            RPM: numberVal(RPM),
            consumption_lh: numberVal(consumptionLh),
            consumption_l100km: numberVal(consumptionL100km),
            Speed: numberVal(Speed),
            CO: numberVal(CO),
            HC: numberVal(HC),
            CO2: numberVal(CO2),
            O2: numberVal(O2),
            Lambda: numberVal(Lambda),
            AFR: numberVal(AFR),
        };

        if (!telemetryFetched) {
            const sLower = `${symptoms} ${warningLight}`.toLowerCase();
            if (sLower.includes("battery") || sLower.includes("click") || sLower.includes("voltage") || sLower.includes("dead")) {
                telemetryObj = BUILTIN_PRESETS.preset_low_voltage.telemetry;
            } else if (sLower.includes("tire") || sLower.includes("flat") || sLower.includes("puncture") || sLower.includes("wheel")) {
                telemetryObj = BUILTIN_PRESETS.preset_tire_damage.telemetry;
            } else if (sLower.includes("hesitat") || sLower.includes("surging") || sLower.includes("lean") || sLower.includes("vacuum")) {
                telemetryObj = BUILTIN_PRESETS.preset_lean_mixture.telemetry;
            } else if (sLower.includes("smoke") || sLower.includes("misfire") || sLower.includes("rich")) {
                telemetryObj = BUILTIN_PRESETS.preset_rich_mixture.telemetry;
            }
        }

        const breakdownData: BreakdownData = {
            vehicleModel: vehicleModel.trim(),
            vehicleYear: vehicleYear.trim() || "2022",
            vehicleType,
            fuelType,
            symptoms: symptoms.trim(),
            warningLight: warningLight.trim() || "Warning indicator light active",
            location: location.trim() || "Koramangala, Bengaluru",
            latitude: latitude ?? 12.9345,
            longitude: longitude ?? 77.6265,
            enginePhoto: enginePhoto || undefined,
            ...telemetryObj,
        };

        setLoading(true);

        try {
            onComplete(breakdownData);
        } catch (submitError) {
            console.error("Submission error:", submitError);
            setError("Unable to submit breakdown report.");
            setLoading(false);
        }
    };

    return (
        <div className="page breakdown-page">
            <div className="breakdown-container">
                {/* Header Navbar */}
                <header className="breakdown-header">
                    <button
                        type="button"
                        className="back-button"
                        onClick={onBack}
                        disabled={loading}
                        aria-label="Go back"
                    >
                        ← Back to Home
                    </button>

                    <div className="header-title-group">
                        <span className="badge-pill pulse-badge">🚨 Guided Roadside Assistance</span>
                        <h1>Report Vehicle Breakdown</h1>
                        <p>Fill in details below or click 1-touch chips to auto-fetch diagnostics & dispatch nearest providers</p>
                    </div>
                </header>

                {error && (
                    <div className="alert-box alert-error" role="alert">
                        ⚠️ {error}
                    </div>
                )}

                {successMsg && (
                    <div className="alert-box alert-success" role="status">
                        ✅ {successMsg}
                    </div>
                )}

                <form className="breakdown-form" onSubmit={handleSubmit}>
                    {/* SECTION 1: VEHICLE INFORMATION WITH BRAND CHIPS */}
                    <section className="form-card glass-card">
                        <div className="section-heading">
                            <div className="section-icon">🚗</div>
                            <div>
                                <h2>1. Vehicle Information</h2>
                                <p>Select your vehicle brand or choose from popular models below</p>
                            </div>
                        </div>

                        {/* Quick Pick Brand Chips */}
                        <div className="brand-chips-wrapper">
                            <span className="chips-label">Quick Select Brand:</span>
                            <div className="brand-chips">
                                {QUICK_BRANDS.map((b) => (
                                    <button
                                        key={b.name}
                                        type="button"
                                        className={`brand-chip-btn ${vehicleModel.includes(b.name) ? "active-brand" : ""}`}
                                        onClick={() => handleQuickBrandClick(b)}
                                    >
                                        {b.icon} {b.name}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="form-grid" style={{ marginTop: "16px" }}>
                            <div className="form-group">
                                <label htmlFor="vehicleModel">Vehicle Brand & Model *</label>
                                <input
                                    id="vehicleModel"
                                    type="text"
                                    placeholder="e.g. Honda City / Royal Enfield 350 / Hyundai Creta"
                                    value={vehicleModel}
                                    onChange={(e) => setVehicleModel(e.target.value)}
                                    required
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="vehicleYear">Manufacturing Year</label>
                                <input
                                    id="vehicleYear"
                                    type="text"
                                    placeholder="e.g. 2022"
                                    value={vehicleYear}
                                    onChange={(e) => setVehicleYear(e.target.value)}
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="vehicleType">Vehicle Type Category *</label>
                                <select
                                    id="vehicleType"
                                    value={vehicleType}
                                    className="styled-select"
                                    onChange={(e) => setVehicleType(e.target.value as VehicleType)}
                                    required
                                >
                                    {vehicleCategories.length > 0 ? (
                                        vehicleCategories.map((cat) => (
                                            <optgroup key={cat.category} label={cat.category}>
                                                {cat.vehicles.map((v) => (
                                                    <option key={v.id} value={v.id}>
                                                        {v.icon} {v.name}
                                                    </option>
                                                ))}
                                            </optgroup>
                                        ))
                                    ) : (
                                        <>
                                            <optgroup label="Passenger Vehicles">
                                                <option value="car">🚗 Sedan / Hatchback / Car</option>
                                                <option value="suv">🚙 SUV / Crossover</option>
                                                <option value="pickup_truck">🛻 Pickup Truck</option>
                                            </optgroup>
                                            <optgroup label="Two Wheelers">
                                                <option value="motorcycle">🏍️ Motorcycle / Bike</option>
                                                <option value="scooter">🛵 Scooter / Scooty</option>
                                                <option value="moped">🛵 Moped</option>
                                            </optgroup>
                                            <optgroup label="Auto & Transit">
                                                <option value="auto_rickshaw">🛺 Auto Rickshaw</option>
                                                <option value="e_rickshaw">🛺 E-Rickshaw</option>
                                                <option value="taxi">🚕 Taxi / Cab</option>
                                                <option value="van">🚐 Van / Minivan</option>
                                            </optgroup>
                                            <optgroup label="Commercial & Heavy">
                                                <option value="bus">🚌 Bus / Coach</option>
                                                <option value="truck">🚚 Truck</option>
                                                <option value="mini_truck">🛻 Mini Truck</option>
                                                <option value="light_truck">🚚 Light Commercial Truck</option>
                                                <option value="heavy_truck">🚛 Heavy Truck</option>
                                                <option value="tractor">🚜 Tractor</option>
                                                <option value="ambulance">🚑 Ambulance</option>
                                            </optgroup>
                                        </>
                                    )}
                                </select>
                            </div>

                            <div className="form-group">
                                <label htmlFor="fuelType">Fuel / Powertrain Type *</label>
                                <select
                                    id="fuelType"
                                    value={fuelType}
                                    className="styled-select"
                                    onChange={(e) => setFuelType(e.target.value)}
                                    required
                                >
                                    <option value="Petrol">⛽ Petrol (Gasoline)</option>
                                    <option value="Diesel">⛽ Diesel</option>
                                    <option value="Electric">⚡ Electric (EV)</option>
                                    <option value="CNG">🍃 CNG (Compressed Natural Gas)</option>
                                    <option value="Hybrid">🔋 Hybrid (Petrol + Electric)</option>
                                    <option value="PHEV">🔋 Plug-in Hybrid (PHEV)</option>
                                    <option value="LPG">🍃 LPG (Liquefied Petroleum Gas)</option>
                                </select>
                            </div>
                        </div>
                    </section>

                    {/* SECTION 2: BREAKDOWN SYMPTOMS WITH 1-TOUCH SYMPTOM CARDS & IMAGE UPLOAD */}
                    <section className="form-card glass-card">
                        <div className="section-heading">
                            <div className="section-icon">📍</div>
                            <div>
                                <h2>2. Breakdown Symptoms & Location</h2>
                                <p>Click a symptom card or upload engine photos for AI diagnostic analysis</p>
                            </div>
                        </div>

                        {/* Interactive 1-Touch Symptom Selector Cards */}
                        <div className="symptoms-selector-wrapper">
                            <span className="chips-label">Quick Select Observed Symptom:</span>
                            <div className="symptom-cards-grid">
                                {QUICK_SYMPTOMS.map((s) => (
                                    <div
                                        key={s.id}
                                        className={`symptom-card-item ${activeSymptomId === s.id ? "active-symptom-card" : ""}`}
                                        onClick={() => handleQuickSymptomClick(s)}
                                    >
                                        <div className="symptom-card-icon">{s.icon}</div>
                                        <div className="symptom-card-info">
                                            <h4>{s.title}</h4>
                                            <p>{s.symptomText.slice(0, 55)}...</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="form-group" style={{ marginTop: "18px" }}>
                            <div className="label-with-action-row">
                                <label htmlFor="symptoms">Symptoms / Problem Description *</label>
                                <button
                                    type="button"
                                    className={`btn-voice-input ${isListening ? "listening-active" : ""}`}
                                    onClick={handleToggleVoiceInput}
                                    title="Speak your problem description"
                                >
                                    {isListening ? "🔴 Listening... (Click to Stop)" : "🎤 Start Voice Recording"}
                                </button>
                            </div>
                            <textarea
                                id="symptoms"
                                rows={3}
                                placeholder="Describe what happened (e.g. 'My car suddenly stopped and the engine is making a clicking noise')..."
                                value={symptoms}
                                onChange={(e) => setSymptoms(e.target.value)}
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="warningLight">Dashboard Warning Indicator</label>
                            <input
                                id="warningLight"
                                type="text"
                                placeholder="e.g. Check Engine Light, Battery Symbol, Oil Light"
                                value={warningLight}
                                onChange={(e) => setWarningLight(e.target.value)}
                            />
                        </div>

                        {/* ENGINE & DAMAGE PHOTO UPLOADER OPTION */}
                        <div className="form-group photo-uploader-group">
                            <label>📷 Vehicle Condition & Damage Photos (CV Visual Analysis)</label>
                            <p className="photo-hint-text">Take or upload a photo of your engine bay, dashboard warning light, or damaged tire for visual diagnosis.</p>

                            {!enginePhoto ? (
                                <div className="photo-actions-box">
                                    <div
                                        className="photo-dropzone"
                                        onClick={() => fileInputRef.current?.click()}
                                    >
                                        <div className="dropzone-icon">📷</div>
                                        <div className="dropzone-text">
                                            <span>Click or drag image to upload photo</span>
                                            <small>Supports PNG, JPG, WEBP (Max 5MB)</small>
                                        </div>
                                    </div>

                                    <div className="photo-buttons-row">
                                        <button
                                            type="button"
                                            className="btn-photo-action"
                                            onClick={() => cameraInputRef.current?.click()}
                                        >
                                            📷 Take Photo
                                        </button>
                                        <button
                                            type="button"
                                            className="btn-photo-action btn-photo-secondary"
                                            onClick={() => fileInputRef.current?.click()}
                                        >
                                            📁 Upload Image
                                        </button>
                                    </div>

                                    <input
                                        ref={fileInputRef}
                                        type="file"
                                        accept="image/*"
                                        onChange={handleImageUpload}
                                        style={{ display: "none" }}
                                    />

                                    <input
                                        ref={cameraInputRef}
                                        type="file"
                                        accept="image/*"
                                        capture="environment"
                                        onChange={handleImageUpload}
                                        style={{ display: "none" }}
                                    />
                                </div>
                            ) : (
                                <div className="photo-preview-card">
                                    <div className="preview-image-container">
                                        <img src={enginePhoto} alt="Engine Breakdown Attachment" className="preview-img" />
                                    </div>
                                    <div className="preview-info">
                                        <span className="preview-status">✅ Photo Attached</span>
                                        <span className="preview-filename">{photoName || "engine_photo.jpg"}</span>
                                        <small>Attached for ML visual diagnosis & technician dispatch</small>
                                    </div>
                                    <button
                                        type="button"
                                        className="btn-remove-photo"
                                        onClick={handleRemoveImage}
                                    >
                                        🗑️ Remove
                                    </button>
                                </div>
                            )}
                        </div>

                        <div className="form-group" style={{ marginTop: "18px" }}>
                            <label>Breakdown Location (Bengaluru Region) *</label>
                            <div className="location-row">
                                <input
                                    type="text"
                                    className="location-input-field"
                                    value={location}
                                    onChange={(e) => setLocation(e.target.value)}
                                    placeholder="Enter street, area, or landmark in Bengaluru"
                                    required
                                />

                                <button
                                    type="button"
                                    className="btn-location-gps"
                                    onClick={getCurrentLocation}
                                    disabled={locationLoading}
                                >
                                    {locationLoading ? "📡 Detecting..." : "🎯 Detect GPS"}
                                </button>
                            </div>

                            {/* Preset Location Quick-Chips */}
                            <div className="preset-locations-wrapper">
                                <span className="chips-label">Quick Pick Location:</span>
                                <div className="location-chips">
                                    {BENGALURU_PRESETS.map((p) => (
                                        <button
                                            key={p.name}
                                            type="button"
                                            className={`chip-btn ${location === p.name ? "active-chip" : ""}`}
                                            onClick={() => handleSelectPresetLocation(p)}
                                        >
                                            📍 {p.name}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* SECTION 3: AUTOMATED VEHICLE DIAGNOSTIC TELEMETRY (ECU DATABASE) */}
                    <section className="form-card glass-card diagnostic-section">
                        <div className="section-heading">
                            <div className="section-icon">⚡</div>
                            <div>
                                <div className="badge-pill success-badge">Automated Backend Diagnostics</div>
                                <h2>3. Automated Vehicle Health & Sensor Check</h2>
                                <p>Vehicle telemetry is scanned automatically from backend database to verify fault severity.</p>
                            </div>
                        </div>

                        <div className="ecu-fetch-panel">
                            <div className="ecu-action-row">
                                <div className="preset-dropdown-group">
                                    <label htmlFor="diagnosticPreset">Detected Health Profile & Diagnostics:</label>
                                    <select
                                        id="diagnosticPreset"
                                        value={selectedPresetId}
                                        onChange={(e) => {
                                            const found = presets.find(p => p.id === e.target.value);
                                            if (found) applyPresetValues(found);
                                        }}
                                        className="styled-select preset-select"
                                    >
                                        {presets.length > 0 ? (
                                            presets.map((p) => (
                                                <option key={p.id} value={p.id}>
                                                    {p.name}
                                                </option>
                                            ))
                                        ) : (
                                            <>
                                                <option value="preset_tire_damage">Flat Tire & Wheel Puncture Damage</option>
                                                <option value="preset_rich_mixture">Engine Misfire & Fuel Injection Issue</option>
                                                <option value="preset_low_voltage">Battery Dead & Low Alternator Voltage</option>
                                                <option value="preset_lean_mixture">Engine Hesitation & Vacuum Air Leak</option>
                                                <option value="preset_normal">Standard Inspection (Normal Vehicle Health)</option>
                                            </>
                                        )}
                                    </select>
                                </div>

                                <button
                                    type="button"
                                    className="btn-scan-ecu"
                                    onClick={handleAutoScanECU}
                                    disabled={isScanningECU}
                                >
                                    {isScanningECU ? "🔄 Scanning ECU Database..." : "⚡ Scan Live OBD-II Database"}
                                </button>
                            </div>

                            {/* VISUAL DASHBOARD DISPLAY OF FETCHED TELEMETRY */}
                            {telemetryFetched ? (
                                <div className="telemetry-dashboard">
                                    <div className="gauge-card">
                                        <span className="gauge-label">RPM</span>
                                        <span className="gauge-value highlight-cyan">{RPM}</span>
                                        <span className="gauge-sub">Engine Revs</span>
                                    </div>

                                    <div className="gauge-card">
                                        <span className="gauge-label">Air-Fuel Ratio</span>
                                        <span className={`gauge-value ${Number(AFR) < 14 ? "highlight-red" : Number(AFR) > 16 ? "highlight-orange" : "highlight-green"}`}>
                                            {AFR}
                                        </span>
                                        <span className="gauge-sub">Lambda: {Lambda}</span>
                                    </div>

                                    <div className="gauge-card">
                                        <span className="gauge-label">MAP Pressure</span>
                                        <span className="gauge-value">{MAP} kPa</span>
                                        <span className="gauge-sub">TPS: {TPS}%</span>
                                    </div>

                                    <div className="gauge-card">
                                        <span className="gauge-label">Emissions (CO)</span>
                                        <span className={`gauge-value ${Number(CO) > 1.5 ? "highlight-red" : "highlight-green"}`}>
                                            {CO}%
                                        </span>
                                        <span className="gauge-sub">HC: {HC} ppm</span>
                                    </div>

                                    <div className="gauge-card">
                                        <span className="gauge-label">Fuel Rate</span>
                                        <span className="gauge-value">{consumptionLh} L/h</span>
                                        <span className="gauge-sub">{consumptionL100km} L/100km</span>
                                    </div>

                                    <div className="gauge-card">
                                        <span className="gauge-label">Speed & Power</span>
                                        <span className="gauge-value">{Speed} km/h</span>
                                        <span className="gauge-sub">Power: {Power} HP</span>
                                    </div>
                                </div>
                            ) : (
                                <div className="telemetry-prompt-box" onClick={handleAutoScanECU}>
                                    <span>👉 Click <b>"⚡ Scan Live OBD-II Database"</b> to auto-load telemetry values from backend database</span>
                                </div>
                            )}

                            {/* Optional Fine-Tune Collapsible Drawer */}
                            <div className="fine-tune-toggle-wrapper">
                                <button
                                    type="button"
                                    className="btn-toggle-fine-tune"
                                    onClick={() => setShowFineTune(!showFineTune)}
                                >
                                    {showFineTune ? "▼ Hide Raw ECU Telemetry Sensors" : "⚙️ View / Adjust Raw ECU Sensors (Optional)"}
                                </button>
                            </div>

                            {showFineTune && (
                                <div className="telemetry-grid fine-tune-grid">
                                    <TelemetryField label="MAP (kPa)" value={MAP} onChange={setMAP} />
                                    <TelemetryField label="TPS (%)" value={TPS} onChange={setTPS} />
                                    <TelemetryField label="Force (N)" value={Force} onChange={setForce} />
                                    <TelemetryField label="Power (HP)" value={Power} onChange={setPower} />
                                    <TelemetryField label="RPM" value={RPM} onChange={setRPM} />
                                    <TelemetryField label="Consumption L/H" value={consumptionLh} onChange={setConsumptionLh} />
                                    <TelemetryField label="Consumption L/100km" value={consumptionL100km} onChange={setConsumptionL100km} />
                                    <TelemetryField label="Speed (km/h)" value={Speed} onChange={setSpeed} />
                                    <TelemetryField label="CO (%)" value={CO} onChange={setCO} />
                                    <TelemetryField label="HC (ppm)" value={HC} onChange={setHC} />
                                    <TelemetryField label="CO2 (%)" value={CO2} onChange={setCO2} />
                                    <TelemetryField label="O2 (%)" value={O2} onChange={setO2} />
                                    <TelemetryField label="Lambda" value={Lambda} onChange={setLambda} />
                                    <TelemetryField label="AFR" value={AFR} onChange={setAFR} />
                                </div>
                            )}
                        </div>
                    </section>

                    {/* ACTIONS */}
                    <div className="breakdown-actions">
                        <button
                            type="button"
                            className="secondary-button"
                            onClick={onBack}
                            disabled={loading}
                        >
                            Cancel
                        </button>

                        <button
                            type="submit"
                            className="primary-button btn-analyze"
                            disabled={loading}
                        >
                            {loading ? "🔄 Dispatching ML Diagnosis..." : "⚡ Analyze & Match Providers"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

interface TelemetryFieldProps {
    label: string;
    value: string;
    onChange: (val: string) => void;
}

function TelemetryField({ label, value, onChange }: TelemetryFieldProps) {
    return (
        <div className="telemetry-input-item">
            <label>{label}</label>
            <input
                type="number"
                step="any"
                value={value}
                onChange={(e) => onChange(e.target.value)}
            />
        </div>
    );
}

export default Breakdown;