import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json

from fastapi.middleware.cors import CORSMiddleware

from shared.logger import get_logger
from q4_live_insights.pipeline import AudioStreamPipeline
from pydantic import BaseModel

# 1. Mount the global web directory
WEB_DIR = Path(__file__).parent.parent / "web"

log = get_logger("q4.server")

# Initialize the FastAPI web server. This will handle HTTP requests and WebSocket connections.
app = FastAPI(title="Live Insights Dashboard")

# Add CORS so dashboards on other domains can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

# This list keeps track of all active browser windows connected to our WebSocket.
# We need this so we can broadcast the live nudges to everyone looking at the dashboard.
active_connections: list[WebSocket] = []

# Global state lock to prevent concurrent audio streams
is_streaming = False

# Global Pipeline for Live Vapi Calls (Q1/Q3 -> Q4 integration)
# We initialize it lazily when the first route is called so the event loop is ready.
global_pipeline = None

class TranscriptPayload(BaseModel):
    text: str
    is_final: bool

@app.websocket("/ws/nudges")
async def websocket_endpoint(websocket: WebSocket):
    # Accept the incoming connection from the browser
    await websocket.accept()
    # Add the connection to our list of active clients
    active_connections.append(websocket)
    log.info("ws_client_connected")
    try:
        while True:
            # Just keep the connection alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        log.info("ws_client_disconnected")

async def broadcast_nudge(nudge_type: str, message: str, context: dict = None):
    """
    Called by the audio pipeline when a nudge is generated (e.g. frustration detected).
    Sends the nudge as a JSON string to all connected browser dashboards.
    """
    payload = {
        "type": nudge_type,
        "message": message,
        "context": context or {}
    }
    # Loop through every connected browser and send the data
    dead_connections = []
    for connection in active_connections:
        try:
            await connection.send_text(json.dumps(payload))
        except Exception as e:
            dead_connections.append(connection)
            log.error("ws_broadcast_failed", error=str(e))
            
    for dc in dead_connections:
        if dc in active_connections:
            active_connections.remove(dc)

async def broadcast_transcript(text: str, is_final: bool):
    """Stream live transcripts to the UI for visibility."""
    payload = {
        "type": "transcript",
        "text": text,
        "is_final": is_final
    }
    dead_connections = []
    for connection in active_connections:
        try:
            await connection.send_text(json.dumps(payload))
        except Exception as e:
            dead_connections.append(connection)
            
    for dc in dead_connections:
        if dc in active_connections:
            active_connections.remove(dc)

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serves the new unified dashboard."""
    index_file = WEB_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Dashboard UI not built yet.")
    return index_file.read_text()

@app.post("/start_stream")
async def start_stream(background_tasks: BackgroundTasks):
    global is_streaming
    
    if is_streaming:
        log.warning("stream_already_running")
        raise HTTPException(status_code=409, detail="A stream is already running.")
        
    is_streaming = True
    
    try:
        # In a real app, this would be triggered by a Vapi webhook when a call connects.
        # For the assessment, we simulate it by reading a local file.
        wav_path = Path(__file__).parent / "test_calls" / "audio_0.wav"
        
        if not wav_path.exists():
            is_streaming = False
            return {"error": "Test audio file not found. Place a wav file at q4_live_insights/test_calls/mock_call.wav"}
            
        pipeline = AudioStreamPipeline(
            on_nudge=broadcast_nudge,
            on_transcript=broadcast_transcript
        )
        
        # Wrap the pipeline in a background task that resets the lock when done
        async def run_pipeline_with_lock():
            global is_streaming
            try:
                await pipeline.process_file(str(wav_path))
            finally:
                is_streaming = False
                
        background_tasks.add_task(run_pipeline_with_lock)
        return {"status": "Stream started in background"}
    except Exception as e:
        is_streaming = False
        raise e

@app.post("/analyze_transcript_direct")
async def analyze_transcript_direct(payload: TranscriptPayload):
    """
    Called by the web frontend (app.js) whenever Vapi streams a transcript.
    Passes it directly into the Q4 pipeline to trigger nudges.
    """
    global global_pipeline
    if not global_pipeline:
        global_pipeline = AudioStreamPipeline(
            on_nudge=broadcast_nudge,
            on_transcript=broadcast_transcript
        )
        global_pipeline.start()
    
    # Pass to the analyzer which runs the Nudge Engine
    import time
    global_pipeline.add_transcript(payload.text, payload.is_final, time.time())
    return {"status": "queued"}

if __name__ == "__main__":
    import uvicorn
    import sys
    log.warning("You ran the old server command. Automatically redirecting to the new Unified Global Server...")
    # Import the global app
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from server import app as global_app
    uvicorn.run(global_app, host="0.0.0.0", port=8080)
