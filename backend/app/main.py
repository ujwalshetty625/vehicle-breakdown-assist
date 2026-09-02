from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.providers import router as providers_router
from app.api.match_provider import router as match_provider_router
from app.api.replan import router as replan_router
from app.api.diagnose import router as diagnose_router
from app.api.assist import router as assist_router
from app.api.vehicle_types import router as vehicle_types_router
from app.api.diagnostics import router as diagnostics_router

app = FastAPI(title="Vehicle Breakdown Assist")

# Add CORS Middleware so frontend can make request from localhost:5173 / localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(providers_router)
app.include_router(match_provider_router)
app.include_router(replan_router)
app.include_router(diagnose_router)
app.include_router(assist_router)
app.include_router(vehicle_types_router)
app.include_router(diagnostics_router)

@app.get("/")
def root():
    return {"status": "ok", "message": "Vehicle Breakdown Assist API is running"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "vehicle-breakdown-assist"}