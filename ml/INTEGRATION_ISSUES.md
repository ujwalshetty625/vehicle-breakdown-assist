# Integration Audit & Issues Log

**Project**: Intelligent Multimodal Vehicle Breakdown Assistance and Adaptive Recovery System  
**Audit Date**: September 2026  
**Auditor**: Vishal (ML Module Lead)

---

## 1. Executive Summary

An end-to-end integration audit was conducted across the **Machine Learning (ML)**, **Backend (FastAPI)**, and **Frontend (React + Vite)** subsystems. The ML module artifacts and backend model loading functions are 100% verified and operating with real inference outputs. Below are the specific integration notes and suggestions logged for backend (Ujwal) and frontend (Waleed).

---

## 2. Integration Findings & Suggestions for Team

### Issue 1: CORS Middleware Configuration in Backend
- **Module / Owner**: Backend (`Ujwal`)
- **File**: `backend/app/main.py`
- **Observation**: When running the React frontend on `http://localhost:5173` (Vite) and the FastAPI backend on `http://localhost:8000`, browser cross-origin security blocks HTTP requests unless `CORSMiddleware` is registered.
- **Suggested Fix**: Keep `CORSMiddleware` configured in `backend/app/main.py` with `allow_origins=["*"]` (or `["http://localhost:5173"]`), `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]`.

---

### Issue 2: Frontend Form Telemetry vs Sensor Data Mapping
- **Module / Owner**: Frontend (`Waleed`) & Backend (`Ujwal`)
- **File**: `frontend/src/api/api.ts` and `frontend/src/pages/Breakdown.tsx`
- **Observation**: The breakdown intake form collects driver-entered symptoms (text description, warning lights dropdown, vehicle model/year). The ML engine is trained on 14 numeric OBD-II engine sensor telemetry features (`MAP`, `TPS`, `CO`, `HC`, `Lambda`, `AFR`, etc.).
- **Current Resolution**: The backend provides `/assist` which accepts user vehicle info alongside default/simulated sensor telemetry or symptom heuristics to bridge driver input with ML inference.
- **Future Enhancement**: Add an optional "Upload OBD-II / Sensor Telemetry JSON" toggle on the frontend form so advanced users can test real sensor telemetry directly.

---

### Issue 3: Warning Light Dropdown to Computer Vision Pipeline Transition
- **Module / Owner**: Frontend (`Waleed`) & Backend (`Ujwal`)
- **File**: `frontend/src/pages/Breakdown.tsx`
- **Observation**: Currently, the warning light is selected manually via a dropdown menu.
- **Next Step (Phase 3 CV)**: The new Computer Vision module (`ml/cv_model_card.md`) will allow users to upload a dashboard photo (`POST /vision/analyze`), which infers the active warning light automatically and populates the breakdown diagnosis flow.

---

## 3. ML Module Verification Status

| Checklist Item | Scope | Status | Notes |
|:---|:---:|:---:|:---|
| `model.pkl` Artifact | ML | ✅ Verified | Loads without error (RandomForestClassifier, 200 trees, 17.87 MB). |
| `scaler.pkl` Artifact | ML | ✅ Verified | Matches 14 features, fitted on training set only. |
| `feature_order.json` | ML | ✅ Verified | 14 canonical sensor features matching training schema. |
| `labels.json` | ML | ✅ Verified | Exact mapping: 0=No Fault, 1=Rich Mixture, 2=Lean Mixture, 3=Low Voltage. |
| Model Card Contract | ML | ✅ Verified | `ml/model_card.md` documents exact I/O, changelog, and voltage limitation. |
| Backend `/diagnose` | Backend / ML | ✅ Verified | Successfully returns real ML predictions and class probabilities. |
| Backend `/assist` | Backend / ML | ✅ Verified | Runs ML diagnosis ➔ Capability Resolution ➔ Provider Matching. |
| Database Seed | Backend | ✅ Verified | SQLite `breakdown_assist.db` initialized with real Bengaluru providers. |
