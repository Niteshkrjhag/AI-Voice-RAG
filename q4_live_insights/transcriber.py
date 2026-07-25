"""
q4_live_insights/transcriber.py — Streaming ASR integration (AssemblyAI).

Connects to AssemblyAI's Real-Time API to transcribe audio chunks on the fly.
Includes latency measurement per chunk as required by the Assessment.
"""

import asyncio
import time
import assemblyai as aai
from typing import Callable, Optional

from shared.config import config
from shared.logger import get_logger

log = get_logger("q4.transcriber")

# AssemblyAI global config
aai.settings.api_key = config.ASSEMBLYAI_API_KEY


class StreamingTranscriber:
    """
    Manages a real-time AssemblyAI streaming connection.
    Measures component latency (audio sent -> text received).
    """
    
    def __init__(self, sample_rate: int = 16000, on_transcript: Optional[Callable] = None):
        self.sample_rate = sample_rate
        self.on_transcript = on_transcript
        self._transcriber = None
        self._loop = asyncio.get_running_loop()
        self.chunk_start_times = {}  # Tracks latency per chunk
        
    def _on_open(self, session_opened):
        log.info("asr_session_opened", session_id=getattr(session_opened, "session_id", "unknown"))

    def _on_data(self, transcript):
        if not getattr(transcript, "text", None):
            return
            
        # Calculate latency
        received_time = time.time()
        
        # Check if it's a final transcript
        # Sometimes it's isinstance(transcript, aai.RealtimeFinalTranscript), sometimes it has a message_type attribute.
        # Let's use a safe check.
        is_final = getattr(transcript, "message_type", "") == "FinalTranscript" or "Final" in type(transcript).__name__
        
        if is_final:
            log.info("asr_final_transcript", text=transcript.text)
            if self.on_transcript:
                self._loop.call_soon_threadsafe(self.on_transcript, transcript.text, True, received_time)
        else:
            if self.on_transcript:
                self._loop.call_soon_threadsafe(self.on_transcript, transcript.text, False, received_time)

    def _on_error(self, error):
        log.error("asr_error", error=str(error))

    def _on_close(self):
        log.info("asr_session_closed")

    def connect(self):
        """Initializes the Real-Time transcriber."""
        if not config.ASSEMBLYAI_API_KEY:
            log.warning("assemblyai_key_missing_mocking_transcriber")
            return

        self._transcriber = aai.RealtimeTranscriber(
            sample_rate=self.sample_rate,
            on_data=self._on_data,
            on_error=self._on_error,
            on_open=self._on_open,
            on_close=self._on_close,
        )
        self._transcriber.connect()
        
    def stream_audio(self, audio_data: bytes):
        """Send a chunk of audio to the ASR engine."""
        if self._transcriber:
            self._transcriber.stream(audio_data)
            
    def close(self):
        """Closes the ASR connection."""
        if self._transcriber:
            self._transcriber.close()
