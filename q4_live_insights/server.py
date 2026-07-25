import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json

from fastapi.middleware.cors import CORSMiddleware

from shared.logger import get_logger
from q4_live_insights.pipeline import AudioStreamPipeline

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

# This list keeps track of all active browser windows connected to our WebSocket.
# We need this so we can broadcast the live nudges to everyone looking at the dashboard.
active_connections: list[WebSocket] = []

# SDE-3: Global state lock to prevent concurrent audio streams
is_streaming = False

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
    """Serves the main HTML dashboard page when someone visits the root URL (http://localhost:8080/)."""
    html_path = Path(__file__).parent / "templates" / "dashboard.html"
    return html_path.read_text()

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
        wav_path = Path(__file__).parent / "test_audio" / "frustrated_customer.wav"
        
        if not wav_path.exists():
            is_streaming = False
            return {"error": "Test audio file not found. Place a wav file at q4_live_insights/test_audio/frustrated_customer.wav"}
            
        pipeline = AudioStreamPipeline(
            on_nudge=broadcast_nudge,
            on_transcript=broadcast_transcript
        )
        
        # SDE-3: Wrap the pipeline in a background task that resets the lock when done
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
