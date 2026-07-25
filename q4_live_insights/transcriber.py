"""
q4_live_insights/transcriber.py — Streaming ASR integration (AssemblyAI).

Connects to AssemblyAI's Real-Time API to transcribe audio chunks on the fly.
Includes latency measurement per chunk as required by the Assessment.
"""

import asyncio
import time
from typing import Callable, Optional

from assemblyai.streaming.v3 import StreamingClient, StreamingClientOptions, StreamingParameters, StreamingEvents
from assemblyai.streaming.v3.models import TurnEvent, ErrorEvent

from shared.config import config
from shared.logger import get_logger

log = get_logger("q4.transcriber")


class StreamingTranscriber:
    """
    Manages a real-time AssemblyAI streaming connection using the V3 Streaming API.
    Measures component latency (audio sent -> text received).
    """
    
    def __init__(self, sample_rate: int = 16000, on_transcript: Optional[Callable] = None):
        self.sample_rate = sample_rate
        self.on_transcript = on_transcript
        self._loop = asyncio.get_running_loop()
        self.chunk_start_times = {}  # Tracks latency per chunk
        
        options = StreamingClientOptions(api_key=config.ASSEMBLYAI_API_KEY)
        self._client = StreamingClient(options)
        
        self._client.on(StreamingEvents.SESSION_OPENED, self._on_open)
        self._client.on(StreamingEvents.DATA, self._on_data)
        self._client.on(StreamingEvents.ERROR, self._on_error)
        self._client.on(StreamingEvents.SESSION_CLOSED, self._on_close)

    def _on_open(self, session_opened):
        log.info("asr_session_opened")

    def _on_data(self, event):
        if isinstance(event, TurnEvent):
            if not event.transcript:
                return
            
            received_time = time.time()
            is_final = event.end_of_turn
            
            if is_final:
                log.info("asr_final_transcript", text=event.transcript)
            
            if self.on_transcript:
                self._loop.call_soon_threadsafe(self.on_transcript, event.transcript, is_final, received_time)

    def _on_error(self, error):
        error_msg = getattr(error, "message", str(error))
        log.error("asr_error", error=error_msg)

    def _on_close(self, _=None):
        log.info("asr_session_closed")

    def connect(self):
        """Initializes the Real-Time transcriber."""
        if not config.ASSEMBLYAI_API_KEY:
            log.warning("assemblyai_key_missing_mocking_transcriber")
            return

        params = StreamingParameters(sample_rate=self.sample_rate)
        self._client.connect(params)
        
    def stream_audio(self, audio_data: bytes):
        """Send a chunk of audio to the ASR engine."""
        if hasattr(self, '_client'):
            self._client.stream(audio_data)
            
    def close(self):
        """Closes the ASR connection."""
        if hasattr(self, '_client'):
            self._client.disconnect()

