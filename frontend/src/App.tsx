import { useState } from "react";

import Home from "./pages/Home";
import Breakdown from "./pages/Breakdown";
import Results from "./pages/Results";

import type { Provider } from "./types/vehicle";

type Page = "home" | "breakdown" | "results";

function App() {
    const [page, setPage] = useState<Page>("home");

    const [providers, setProviders] = useState<Provider[]>([]);

    const handleAnalysisComplete = () => {

        /*
         * TEMPORARY PROVIDER DATA
         *
         * This is only for frontend testing.
         *
         * Later:
         * Ujwal's FastAPI backend
         *        ↓
         * Provider database
         *        ↓
         * Intelligent matching
         *        ↓
         * Providers returned here
         */

        const dummyProviders: Provider[] = [

            {
                id: 1,

                name: "BatteryFix Roadside Services",

                latitude: 12.915,
                longitude: 77.565,

                distanceKm: 3.2,
                etaMinutes: 11,

                rating: 4.7,

                available: true,

                services: [
                    "Battery",
                    "Electrical",
                    "Jump Start",
                ],

                vehicleCompatibility: [
                    "Petrol",
                    "Diesel",
                    "Hybrid",
                ],

                matchScore: 92,
            },


            {
                id: 2,

                name: "AutoCare Emergency Services",

                latitude: 12.920,
                longitude: 77.570,

                distanceKm: 5.1,
                etaMinutes: 17,

                rating: 4.5,

                available: true,

                services: [
                    "Battery",
                    "Tyre",
                    "Towing",
                ],

                vehicleCompatibility: [
                    "Petrol",
                    "Diesel",
                ],

                matchScore: 84,
            },

        ];

        // Store providers
        setProviders(dummyProviders);

        // Move to Results page
        setPage("results");
    };


    /*
     * BREAKDOWN PAGE
     */

    if (page === "breakdown") {

        return (
            <Breakdown
                onBack={() => setPage("home")}
                onComplete={handleAnalysisComplete}
            />
        );

    }


    /*
     * RESULTS PAGE
     */

    if (page === "results") {

        return (
            <Results
                onBack={() => setPage("breakdown")}
                providers={providers}
            />
        );

    }


    /*
     * HOME PAGE
     */

    return (
        <Home
            onReport={() => setPage("breakdown")}
        />
    );
}

export default App;