"""
q4_live_insights/signal_extractor.py — Real-time intent and risk detection.

Uses Gemini to analyze partial and final transcripts to detect:
- Buying signals / Cross-sell opportunities
- Frustration / Sentiment drops
- Compliance risks (e.g. missing disclosures)
"""

import time
import json
from google import genai
from google.genai import types

from shared.config import config
from shared.logger import get_logger

log = get_logger("q4.signal_extractor")

# Initialize 2026 standard genai Client
# No global configure() - we use the client directly
client = genai.Client(api_key=config.GOOGLE_API_KEY)


class SignalExtractor:
    def __init__(self):
        self.system_prompt = (
            "You are a real-time call monitoring AI for a health insurance call center. "
            "Analyze the latest transcript segment and return a JSON object with any detected signals. "
            "Focus ONLY on: 'missed_cross_sell', 'compliance_gap', 'frustration'. "
            "If none, return empty JSON {}."
        )

    async def analyze_transcript(self, text: str, full_context: str) -> dict:
        """
        Analyze the transcript for actionable signals.
        Returns the parsed JSON and the latency of the LLM call.
        """
        if not text.strip():
            return {"signals": {}, "latency_ms": 0}

        start_time = time.time()
        
        prompt = f"Previous Context: {full_context[-500:]}\nLatest utterance: {text}"
        
        try:
            # We use the fast Gemini Flash model for real-time latency
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            try:
                signals = json.loads(response.text)
            except json.JSONDecodeError:
                signals = {}
                
            log.debug("signal_extracted", signals=signals, latency_ms=latency_ms)
            return {"signals": signals, "latency_ms": latency_ms}
            
        except Exception as e:
            log.error("signal_extraction_failed", error=str(e))
            return {"signals": {}, "latency_ms": 0}
