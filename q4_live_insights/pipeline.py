import asyncio
import time
from shared.logger import get_logger

from q4_live_insights.transcriber import StreamingTranscriber
from q4_live_insights.signal_extractor import SignalExtractor
from q4_live_insights.nudge_engine import NudgeEngine

log = get_logger("q4.pipeline")

class AudioStreamPipeline:
    """
    Coordinates the flow of audio from simulation into the Transcriber, 
    then to the SignalExtractor, then to the NudgeEngine.
    """
    def __init__(self, on_nudge, on_transcript):
        # We store these callback functions so we can push data to the web dashboard
        self.on_nudge_callback = on_nudge
        self.on_transcript_callback = on_transcript
        
        # Extractor (Gemini) checks the text for insights
        self.extractor = SignalExtractor()
        # NudgeEngine controls how often alerts are shown (15-second cooldown)
        self.nudge_engine = NudgeEngine(suppression_window_ms=15000)
        
        # We need the full history of the conversation so the AI has context
        self.full_context = ""
        self.pending_text = ""
        
        # Throttler to protect Gemini Free Tier limits (15 seconds)
        self.last_gemini_call = 0
        
        # We'll setup the AssemblyAI transcriber later when the audio actually starts playing
        self.transcriber = None
        
        # Grab the current event loop so we can run background tasks easily
        self._loop = asyncio.get_running_loop()
        
    def start(self):
        """Start the background processing loop."""
        if not hasattr(self, "_flush_task"):
            self._flush_task = asyncio.create_task(self._flush_loop())
            
    def add_transcript(self, text: str, is_final: bool, received_time: float):
        """Called by the frontend or test script to push text."""
        # Update full context if final
        if is_final:
            self.full_context += f" {text}"
            self.pending_text += f" {text}"
            # Prevent unbounded memory leak
            if len(self.full_context) > 4000:
                self.full_context = self.full_context[-4000:]
                
        # Fire off UI update
        asyncio.create_task(self.on_transcript_callback(text, is_final))
        
    async def _flush_loop(self):
        """Background task that reliably flushes pending text every 15 seconds."""
        while True:
            await asyncio.sleep(15.0)
            
            text_to_analyze = self.pending_text.strip()
            if not text_to_analyze:
                continue
                
            self.pending_text = ""
            start_time = time.time()
                
            try:
                # Ask Gemini (SignalExtractor) what it thinks
                result = await self.extractor.analyze_transcript(text_to_analyze, self.full_context)
                signals = result.get("signals", {})
                
                # Emit telemetry for LLM analysis
                await self.on_nudge_callback(
                    nudge_type="telemetry_update",
                    message="",
                    context={
                        "llm_latency_ms": result.get("latency_ms", 0),
                        "backend_e2e_ms": int((time.time() - start_time) * 1000),
                        "generated_at_ms": time.time() * 1000
                    }
                )
                
                if not signals:
                    continue
                    
                # Check suppression cooldown
                nudges = self.nudge_engine.process_signals(signals)
                
                # Send valid nudges to the Web Dashboard
                for nudge in nudges:
                    e2e_latency = int((time.time() - start_time) * 1000)
                    nudge_generated_at = time.time() * 1000
                    log.info("e2e_latency_measured", llm_latency_ms=result.get("latency_ms", 0), total_e2e_ms=e2e_latency, signal=nudge.get("type"))
                    
                    await self.on_nudge_callback(
                        nudge_type=nudge.get("type", "alert").lower(),
                        message=nudge.get("message", ""),
                        context={
                            "llm_latency_ms": result.get("latency_ms", 0),
                            "backend_e2e_ms": e2e_latency,
                            "generated_at_ms": nudge_generated_at
                        }
                    )
            except Exception as e:
                log.error("flush_loop_failed", error=str(e), text=text_to_analyze)
            
    async def process_file(self, wav_path: str):
        """Simulate a real-time stream by reading a wav file in chunks."""
        self.start()
        
        # We need a wrapper to call add_transcript from the threaded transcriber
        def _handle_transcript_threadsafe(text: str, is_final: bool):
            asyncio.run_coroutine_threadsafe(
                self.on_transcript_callback(text, is_final), self._loop
            )
            if is_final:
                # We can't await add_transcript here easily, so we just mutate state safely
                self.full_context += f" {text}"
                self.pending_text += f" {text}"
                if len(self.full_context) > 4000:
                    self.full_context = self.full_context[-4000:]

        self.transcriber = StreamingTranscriber(on_transcript=_handle_transcript_threadsafe)
        # Offload synchronous WebSocket connection to a background thread
        await asyncio.to_thread(self.transcriber.connect)
        
        log.info("start_simulated_stream", file=wav_path)
        
        # In a real app we'd use aiofiles or a real websocket. 
        # For simulation, we'll just read standard chunks.
        CHUNK_SIZE = 4096 
        
        try:
            # We use asyncio.to_thread to run file I/O operations in a background thread.
            # This prevents standard blocking open() and read() from freezing the async event loop.
            def read_chunk(file_obj):
                return file_obj.read(CHUNK_SIZE)

            f = await asyncio.to_thread(open, wav_path, "rb")
            try:
                while True:
                    data = await asyncio.to_thread(read_chunk, f)
                    if not data:
                        break
                    
                    # Offload synchronous streaming to a background thread
                    await asyncio.to_thread(self.transcriber.stream_audio, data)
                    # Simulate real-time delay (roughly 4096 bytes at 16khz 16-bit mono is ~0.128 seconds)
                    await asyncio.sleep(0.128)
            finally:
                await asyncio.to_thread(f.close)
                    
            log.info("end_simulated_stream")
            
        except Exception as e:
            log.error("stream_error", error=str(e))
        finally:
            # Let the final bits flush
            await asyncio.sleep(2)
            self.transcriber.close()
