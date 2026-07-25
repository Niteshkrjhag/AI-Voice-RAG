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

# 3. Mount existing routers from other sub-applications
app.mount("/q2", q2_app)
app.mount("/q4", q4_app)

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
