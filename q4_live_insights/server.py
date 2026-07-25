import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json

from shared.logger import get_logger
from q4_live_insights.pipeline import AudioStreamPipeline

log = get_logger("q4.server")

app = FastAPI(title="Live Insights Dashboard")

# Track connected WebSocket clients for nudges
active_connections: list[WebSocket] = []

@app.websocket("/ws/nudges")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
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
    """Called by the pipeline when a nudge is generated."""
    payload = {
        "type": nudge_type,
        "message": message,
        "context": context or {}
    }
    for connection in active_connections:
        try:
            await connection.send_text(json.dumps(payload))
        except Exception as e:
            log.error("ws_broadcast_failed", error=str(e))

async def broadcast_transcript(text: str, is_final: bool):
    """Stream live transcripts to the UI for visibility."""
    payload = {
        "type": "transcript",
        "text": text,
        "is_final": is_final
    }
    for connection in active_connections:
        try:
            await connection.send_text(json.dumps(payload))
        except Exception as e:
            pass

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    html_path = Path(__file__).parent / "templates" / "dashboard.html"
    return html_path.read_text()

@app.post("/start_stream")
async def start_stream():
    """Trigger the simulated audio stream."""
    # Run the pipeline in the background
    asyncio.create_task(run_mock_pipeline())
    return {"status": "Stream started"}

async def run_mock_pipeline():
    pipeline = AudioStreamPipeline(
        on_nudge=broadcast_nudge,
        on_transcript=broadcast_transcript
    )
    
    # Path to a mock wav file
    mock_audio_path = Path(__file__).parent / "test_calls" / "mock_call.wav"
    
    if not mock_audio_path.exists():
        log.warning("mock_audio_missing", path=str(mock_audio_path))
        await broadcast_nudge("error", f"Missing audio file at {mock_audio_path}. Please create a sample wav file.")
        return
        
    await pipeline.process_file(str(mock_audio_path))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
