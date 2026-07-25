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
        
        # We'll setup the AssemblyAI transcriber later when the audio actually starts playing
        self.transcriber = None
        
        # Grab the current event loop so we can run background tasks easily
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
        """
        Takes the spoken text, asks Gemini to find signals (like anger or sales opportunities),
        and then passes those signals to the Nudge Engine to decide if an alert should be shown.
        """
        # We only want to run the expensive AI extraction when a sentence is fully finished (is_final).
        # Running it on every single partial word would waste a lot of money and time.
        if not is_final:
            return
            
        try:
            # Ask Gemini (SignalExtractor) what it thinks about this sentence
            result = await self.extractor.analyze_transcript(text, self.full_context)
            signals = result.get("signals", {})
            
            # If Gemini didn't find anything interesting, just stop here
            if not signals:
                return
                
            # The NudgeEngine checks if we already showed this exact alert recently (suppression cooldown)
            nudges = self.nudge_engine.process_signals(signals)
            
            # Finally, loop through any valid nudges and send them to the Web Dashboard!
            for nudge in nudges:
                await self.on_nudge_callback(
                    nudge_type=nudge.get("type", "alert").lower(),
                    message=nudge.get("message", ""),
                    context={"latency_ms": result.get("latency_ms", 0)}
                )
        except Exception as e:
            log.error("analyze_and_nudge_failed", error=str(e), text=text)
            
    async def process_file(self, wav_path: str):
        """Simulate a real-time stream by reading a wav file in chunks."""
        self.transcriber = StreamingTranscriber(on_transcript=self._handle_transcript)
        self.transcriber.connect()
        
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
                    
                    self.transcriber.stream_audio(data)
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
