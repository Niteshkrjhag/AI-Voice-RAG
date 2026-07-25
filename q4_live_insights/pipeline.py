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
        self.on_nudge_callback = on_nudge
        self.on_transcript_callback = on_transcript
        
        self.extractor = SignalExtractor()
        self.nudge_engine = NudgeEngine(suppression_window_ms=15000)
        
        # We need full context for LLM extraction
        self.full_context = ""
        
        # We'll setup the transcriber later, bound to an asyncio event loop
        self.transcriber = None
        self._loop = asyncio.get_running_loop()
        
    def _handle_transcript(self, text: str, is_final: bool, received_time: float):
        """Called by transcriber thread via call_soon_threadsafe"""
        # Fire off UI update
        asyncio.run_coroutine_threadsafe(self.on_transcript_callback(text, is_final), self._loop)
        
        # Update full context if final
        if is_final:
            self.full_context += f" {text}"
            
        # Analyze transcript (fire and forget so it doesn't block audio ingestion)
        asyncio.run_coroutine_threadsafe(self._analyze_and_nudge(text, is_final), self._loop)
            
    async def _analyze_and_nudge(self, text: str, is_final: bool):
        # We might only want to run extraction on final transcripts or long partials
        # For this demo, let's just do it on finals to save LLM tokens.
        if not is_final:
            return
            
        result = await self.extractor.analyze_transcript(text, self.full_context)
        signals = result.get("signals", {})
        
        if not signals:
            return
            
        nudges = self.nudge_engine.process_signals(signals)
        for nudge in nudges:
            await self.on_nudge_callback(
                nudge_type=nudge.get("type", "alert").lower(),
                message=nudge.get("message", ""),
                context={"latency_ms": result.get("latency_ms", 0)}
            )
            
    async def process_file(self, wav_path: str):
        """Simulate a real-time stream by reading a wav file in chunks."""
        self.transcriber = StreamingTranscriber(on_transcript=self._handle_transcript)
        self.transcriber.connect()
        
        log.info("start_simulated_stream", file=wav_path)
        
        # In a real app we'd use aiofiles or a real websocket. 
        # For simulation, we'll just read standard chunks.
        CHUNK_SIZE = 4096 
        
        try:
            with open(wav_path, "rb") as f:
                while True:
                    data = f.read(CHUNK_SIZE)
                    if not data:
                        break
                    
                    self.transcriber.stream_audio(data)
                    # Simulate real-time delay (roughly 4096 bytes at 16khz 16-bit mono is ~0.128 seconds)
                    await asyncio.sleep(0.128)
                    
            log.info("end_simulated_stream")
            
        except Exception as e:
            log.error("stream_error", error=str(e))
        finally:
            # Let the final bits flush
            await asyncio.sleep(2)
            self.transcriber.close()
