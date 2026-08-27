from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.providers import router as providers_router
from app.api.match_provider import router as match_provider_router
from app.api.replan import router as replan_router
from app.api.diagnose import router as diagnose_router
from app.api.assist import router as assist_router
from app.api.breakdown import router as breakdown_router

app = FastAPI(title="Vehicle Breakdown Assist")

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
app.include_router(breakdown_router)

@app.get("/")
def root():
    return {"message": "Vehicle Breakdown Assist API is running"}