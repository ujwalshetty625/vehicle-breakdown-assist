import {
    ArrowLeft,
    Car,
    MapPin,
    Upload,
    AlertTriangle,
    Loader2,
    CheckCircle,
} from "lucide-react";

import { useEffect, useState } from "react";

import { analyzeBreakdown } from "../api/api";


interface BreakdownProps {
    onBack: () => void;
    onComplete: () => void;
}


function Breakdown({
    onBack,
    onComplete,
}: BreakdownProps) {

    // =========================================================
    // VEHICLE INFORMATION
    // =========================================================

    const [vehicleModel, setVehicleModel] = useState("");
    const [vehicleYear, setVehicleYear] = useState("");
    const [fuelType, setFuelType] = useState("Petrol");


    // =========================================================
    // BREAKDOWN INFORMATION
    // =========================================================

    const [symptoms, setSymptoms] = useState("");
    const [warningLight, setWarningLight] = useState("");


    // =========================================================
    // LOCATION
    // =========================================================

    const [location, setLocation] = useState("");

    const [latitude, setLatitude] =
        useState<number | null>(null);

    const [longitude, setLongitude] =
        useState<number | null>(null);

    const [locationLoading, setLocationLoading] =
        useState(false);

    const [locationError, setLocationError] =
        useState("");


    // =========================================================
    // IMAGE
    // =========================================================

    const [selectedImage, setSelectedImage] =
        useState<File | null>(null);

    const [imagePreview, setImagePreview] =
        useState<string | null>(null);


    // =========================================================
    // GET CURRENT LOCATION
    // =========================================================

    const getCurrentLocation = () => {

        if (!navigator.geolocation) {

            setLocationError(
                "Geolocation is not supported by your browser."
            );

            return;
        }


        setLocationLoading(true);
        setLocationError("");


        navigator.geolocation.getCurrentPosition(

            (position) => {

                const lat =
                    position.coords.latitude;

                const lng =
                    position.coords.longitude;


                setLatitude(lat);
                setLongitude(lng);


                setLocation(
                    `${lat.toFixed(6)}, ${lng.toFixed(6)}`
                );


                setLocationLoading(false);
            },


            (error) => {

                console.error(
                    "Location error:",
                    error
                );


                setLocationLoading(false);


                setLocationError(
                    "Unable to access your location. Please allow location permission."
                );
            },


            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 60000,
            }

        );

    };


    // =========================================================
    // HANDLE IMAGE SELECTION
    // =========================================================

    const handleImageChange = (
        event: React.ChangeEvent<HTMLInputElement>
    ) => {

        const file =
            event.target.files?.[0];


        if (!file) {
            return;
        }


        setSelectedImage(file);


        const previewUrl =
            URL.createObjectURL(file);


        setImagePreview(previewUrl);

    };


    // =========================================================
    // CLEAN IMAGE PREVIEW URL
    // =========================================================

    useEffect(() => {

        return () => {

            if (imagePreview) {
                URL.revokeObjectURL(imagePreview);
            }

        };

    }, [imagePreview]);


    // =========================================================
    // SUBMIT BREAKDOWN
    // =========================================================

    const handleSubmit = async (
        event: React.FormEvent
    ) => {

        event.preventDefault();


        const breakdownData = {

            vehicleModel,

            vehicleYear,

            fuelType,

            symptoms,

            warningLight,

            location,

            latitude,

            longitude,

        };


        console.log(
            "Sending breakdown:",
            breakdownData
        );


        try {

            /*
             * This will connect to Ujwal's FastAPI
             * backend once it is ready.
             */

            const result =
                await analyzeBreakdown(
                    breakdownData
                );


            console.log(
                "Diagnosis received:",
                result
            );


            onComplete();

        } catch (error) {

            console.error(
                "Breakdown analysis failed:",
                error
            );


            /*
             * Backend is not connected yet.
             *
             * The form itself is working.
             */

            alert(
                "Backend is not connected yet. Your form is working, but the AI service is currently unavailable."
            );

        }

    };


    // =========================================================
    // UI
    // =========================================================

    return (

        <div className="breakdown-page">


            {/* =================================================
                HEADER
            ================================================= */}

            <header className="form-header">

                <button
                    className="back-button"
                    onClick={onBack}
                    type="button"
                >

                    <ArrowLeft size={20} />

                    Back

                </button>


                <div className="form-title">

                    <Car size={24} />

                    <span>
                        Report Breakdown
                    </span>

                </div>

            </header>


            {/* =================================================
                MAIN
            ================================================= */}

            <main className="form-container">


                {/* =================================================
                    INTRO
                ================================================= */}

                <div className="form-intro">

                    <div className="intro-icon">

                        <AlertTriangle
                            size={28}
                        />

                    </div>


                    <div>

                        <h1>
                            Tell us what happened
                        </h1>


                        <p>
                            Provide some information about
                            your vehicle and the breakdown.
                            Our system will analyze the
                            situation and determine the
                            appropriate assistance.
                        </p>

                    </div>

                </div>


                {/* =================================================
                    FORM
                ================================================= */}

                <form onSubmit={handleSubmit}>


                    {/* =================================================
                        VEHICLE INFORMATION
                    ================================================= */}

                    <section className="form-section">

                        <h2>
                            Vehicle Information
                        </h2>


                        <div className="form-grid">


                            {/* VEHICLE MODEL */}

                            <div className="form-group">

                                <label>
                                    Vehicle Model
                                </label>


                                <input
                                    type="text"
                                    placeholder="e.g. Hyundai Creta"
                                    value={vehicleModel}
                                    onChange={(e) =>
                                        setVehicleModel(
                                            e.target.value
                                        )
                                    }
                                    required
                                />

                            </div>


                            {/* VEHICLE YEAR */}

                            <div className="form-group">

                                <label>
                                    Vehicle Year
                                </label>


                                <input
                                    type="number"
                                    placeholder="e.g. 2022"
                                    value={vehicleYear}
                                    onChange={(e) =>
                                        setVehicleYear(
                                            e.target.value
                                        )
                                    }
                                    required
                                />

                            </div>


                            {/* FUEL TYPE */}

                            <div className="form-group">

                                <label>
                                    Fuel Type
                                </label>


                                <select
                                    value={fuelType}
                                    onChange={(e) =>
                                        setFuelType(
                                            e.target.value
                                        )
                                    }
                                >

                                    <option>
                                        Petrol
                                    </option>

                                    <option>
                                        Diesel
                                    </option>

                                    <option>
                                        Electric
                                    </option>

                                    <option>
                                        Hybrid
                                    </option>

                                </select>

                            </div>

                        </div>

                    </section>


                    {/* =================================================
                        BREAKDOWN INFORMATION
                    ================================================= */}

                    <section className="form-section">

                        <h2>
                            Breakdown Information
                        </h2>


                        {/* SYMPTOMS */}

                        <div className="form-group">

                            <label>
                                What symptoms are you experiencing?
                            </label>


                            <textarea
                                placeholder="Describe what happened. Example: Vehicle suddenly stopped and won't start..."
                                value={symptoms}
                                onChange={(e) =>
                                    setSymptoms(
                                        e.target.value
                                    )
                                }
                                rows={5}
                                required
                            />

                        </div>


                        {/* WARNING LIGHT */}

                        <div className="form-group">

                            <label>
                                Warning Light
                            </label>


                            <input
                                type="text"
                                placeholder="e.g. Battery warning light / Check engine"
                                value={warningLight}
                                onChange={(e) =>
                                    setWarningLight(
                                        e.target.value
                                    )
                                }
                            />

                        </div>

                    </section>


                    {/* =================================================
                        LOCATION
                    ================================================= */}

                    <section className="form-section">

                        <h2>
                            Location
                        </h2>


                        <div className="location-box">


                            <div className="location-input-row">


                                {/* LOCATION INPUT */}

                                <div className="input-with-icon">

                                    <MapPin size={19} />


                                    <input
                                        type="text"
                                        placeholder="Enter your current location"
                                        value={location}
                                        onChange={(e) =>
                                            setLocation(
                                                e.target.value
                                            )
                                        }
                                        required
                                    />

                                </div>


                                {/* GPS BUTTON */}

                                <button
                                    type="button"
                                    className="location-button"
                                    onClick={
                                        getCurrentLocation
                                    }
                                    disabled={
                                        locationLoading
                                    }
                                >

                                    {locationLoading ? (

                                        <>

                                            <Loader2
                                                size={18}
                                                className="spin"
                                            />

                                            Detecting...

                                        </>

                                    ) : (

                                        <>

                                            <MapPin
                                                size={18}
                                            />

                                            Use My Location

                                        </>

                                    )}

                                </button>

                            </div>


                            {/* LOCATION SUCCESS */}

                            {latitude !== null &&
                                longitude !== null && (

                                    <div className="location-success">

                                        <CheckCircle
                                            size={18}
                                        />


                                        <span>

                                            Location detected:

                                            {" "}

                                            {latitude.toFixed(6)}

                                            {", "}

                                            {longitude.toFixed(6)}

                                        </span>

                                    </div>

                                )}


                            {/* LOCATION ERROR */}

                            {locationError && (

                                <p className="location-error">

                                    <AlertTriangle
                                        size={16}
                                    />

                                    {locationError}

                                </p>

                            )}

                        </div>

                    </section>


                    {/* =================================================
                        OPTIONAL EVIDENCE
                    ================================================= */}

                    <section className="form-section">

                        <h2>
                            Optional Evidence
                        </h2>


                        <div className="upload-box">

                            <Upload
                                size={28}
                            />


                            <h3>
                                Upload Dashboard / Vehicle Image
                            </h3>


                            <p>
                                Upload an image of the
                                warning light or vehicle
                                condition.
                            </p>


                            {/* FILE INPUT */}

                            <input
                                type="file"
                                accept="image/*"
                                onChange={
                                    handleImageChange
                                }
                            />


                            {/* IMAGE PREVIEW */}

                            {imagePreview && (

                                <div className="image-preview">

                                    <img
                                        src={imagePreview}
                                        alt="Selected vehicle"
                                    />


                                    <p>
                                        {selectedImage?.name}
                                    </p>

                                </div>

                            )}

                        </div>

                    </section>


                    {/* =================================================
                        SUBMIT
                    ================================================= */}

                    <button
                        className="analyze-button"
                        type="submit"
                    >

                        Analyze Breakdown

                    </button>

                </form>

            </main>

        </div>

    );

}


export default Breakdown;