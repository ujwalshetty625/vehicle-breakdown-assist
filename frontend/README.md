# Frontend Portal — Vehicle Breakdown Assist

**Intelligent Multimodal Vehicle Breakdown Assistance and Adaptive Recovery System**

This directory houses the modern, responsive web application for stranded drivers and roadside dispatchers. It provides an intuitive, high-speed interface for reporting vehicle breakdowns, capturing dashboard warning lights, viewing real-time machine learning diagnostics, inspecting interactive provider maps, and managing recovery dispatches.

---

## 🛠️ Technology Stack

- **Framework**: React 18 with TypeScript (`.tsx`)
- **Build Tooling**: Vite 5
- **Mapping & Geolocation**: Leaflet / React-Leaflet with OpenStreetMap tiles
- **Icons & UI Accents**: Lucide React
- **Design Language**: Custom Glassmorphic Dark/Light adaptive design with fluid micro-animations

---

## 📁 Directory Structure

```
frontend/
├── public/                 # Static assets & icons
├── src/
│   ├── api/
│   │   └── api.ts          # Centralized Axios/Fetch API client communicating with FastAPI
│   ├── assets/             # Brand logos & imagery
│   ├── components/         # Reusable UI Components
│   │   ├── BreakdownForm.tsx   # Comprehensive multi-step breakdown intake form
│   │   ├── DiagnosisCard.tsx   # AI confidence meter & fault telemetry breakdown
│   │   ├── InteractiveMap.tsx  # Leaflet interactive map with driver & provider pins
│   │   ├── Navbar.tsx          # Navigation header & theme switcher
│   │   ├── ProviderCard.tsx    # Matched provider details, direct call & replanning action
│   │   └── SafetyCard.tsx      # Context-aware roadside risk card & safety instructions
│   ├── pages/
│   │   ├── Breakdown.tsx   # Main intake portal (Brand presets, symptoms, OBD-II scan, camera)
│   │   ├── Home.tsx        # Landing page & emergency hotline quick access
│   │   └── Results.tsx     # Diagnostic results, live dispatch map, and provider directory
│   ├── types/
│   │   └── vehicle.ts      # TypeScript interfaces for API schemas, providers, and telemetry
│   ├── App.tsx             # Root page router & global state coordinator
│   ├── index.css           # Global design system, color tokens, and responsive layout classes
│   └── main.tsx            # DOM root mounting entrypoint
├── index.html              # HTML5 template
├── package.json            # Dependencies & build scripts
├── tsconfig.json           # TypeScript configuration
└── vite.config.ts          # Vite server & proxy configuration
```

---

## 🚀 Getting Started & Local Development

### 1. Install Node Dependencies
Ensure Node.js (v18+) is installed:
```bash
cd frontend
npm install
```

### 2. Start Local Development Server
```bash
npm run dev
```
The application will launch at `http://localhost:5173`.

### 3. Production Build
```bash
npm run build
```
Generates optimized static production assets in `dist/`.

---

## 🌟 Key User Interface Features

1. **1-Click Vehicle & Landmark Presets**: Quick selection buttons for popular vehicle brands (Honda, Hyundai, Maruti, Tata, Royal Enfield) and regional landmark locations.
2. **Preset Diagnostic Scenarios & Simulated OBD-II Scan**: Test real breakdown modes (`Flat Tire`, `Rich Mixture Misfire`, `Battery Dead`, `Lean Mixture Vacuum Leak`, `Normal Operation`) instantly with real sensor parameters.
3. **Live Dashboard Photo Capture**: Direct integration with mobile camera or local file upload to trigger ResNet-18 visual warning light analysis.
4. **Interactive Dispatch Map**: Visualizes driver coordinates, primary matched recovery vehicle route, and alternative provider pins within a dynamic radius.
5. **Contextual Safety Advisory Card**: Highlights situational roadside risk (`Low`, `Moderate`, `Elevated`, `High`) with time-contextual safety guidance for stranded motorists.
6. **Adaptive Re-planning**: 1-click button on the assigned provider card to re-assign the breakdown to the next qualified candidate if the primary provider is unavailable.
