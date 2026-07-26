import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from shared.logger import get_logger

# Import Q2 API and Q4 Server
from q2_knowledge_base.api import app as q2_app
from q4_live_insights.server import app as q4_app

log = get_logger("unified.server")

# 1. Create the unified FastAPI App
app = FastAPI(
    title="Unified AI Assessment Dashboard",
    description="Consolidates Voice Agent, Knowledge Base, Multilingual Bots, and Live Insights into a single dashboard.",
    version="1.0.0"
)

# 2. Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_headers(request: Request, call_next):
    log.info("incoming_request", path=request.url.path, headers=dict(request.headers))
    response = await call_next(request)
    return response

# 3. Mount existing routers from other sub-applications
app.mount("/q2", q2_app)
app.mount("/q4", q4_app)

class CallbackRequest(BaseModel):
    preferred_time: str
    phone_number: str = None

@app.post("/q1/api/v1/schedule_callback")
async def schedule_callback(payload: CallbackRequest):
    """
    Mock endpoint for the Optional Business Action requirement.
    The Vapi agent hits this tool when the user successfully qualifies.
    """
    log.info("callback_scheduled", preferred_time=payload.preferred_time, phone_number=payload.phone_number)
    return {
        "results": [{
            "status": "success",
            "message": f"Callback successfully scheduled for {payload.preferred_time}. A senior agent will call {payload.phone_number or 'the number on file'}."
        }]
    }

class AuthRequest(BaseModel):
    dob: str
    policy_number: str

@app.post("/q1/api/v1/authenticate")
async def authenticate_caller(payload: AuthRequest):
    """
    Mock endpoint for PII authentication.
    """
    log.info("caller_authenticated", dob=payload.dob, policy_number=payload.policy_number)
    return {
        "results": [{
            "status": "success",
            "message": "Identity verified successfully. You may proceed."
        }]
    }

# 4. Mount the Static Frontend UI (The Dashboard)
WEB_DIR = Path(__file__).parent / "web"
WEB_DIR.mkdir(exist_ok=True)

@app.get("/")
async def serve_dashboard():
    """Serves the main SPA index.html"""
    index_file = WEB_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Dashboard UI not built yet.")
    return FileResponse(index_file)

# Mount web directory for static assets (CSS/JS)
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

if __name__ == "__main__":
    log.info("Starting unified assessment dashboard on http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
