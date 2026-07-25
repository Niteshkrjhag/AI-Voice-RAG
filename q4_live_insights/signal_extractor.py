"""
q4_live_insights/signal_extractor.py — Real-time intent and risk detection.

Uses Gemini to analyze partial and final transcripts to detect:
- Buying signals / Cross-sell opportunities
- Frustration / Sentiment drops
- Compliance risks (e.g. missing disclosures)
"""

import time
import json
import re
import asyncio
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
            "You are a real-time call monitoring AI for a general insurance (auto, home, health) call center. "
            "Analyze the latest transcript segment and return a JSON object with any detected signals. "
            "Focus ONLY on: 'intent_shift', 'compliance_gap', 'frustration', 'buying_signal', 'missed_cross_sell', 'callback_need'. "
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
            def call_gemini():
                return client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=self.system_prompt,
                        response_mime_type="application/json",
                        temperature=0.1
                    )
                )

            # SDE-3 Level Retry Logic (Exponential Backoff)
            max_retries = 3
            response = None
            for attempt in range(max_retries):
                try:
                    response = await asyncio.wait_for(asyncio.to_thread(call_gemini), timeout=20.0)
                    break
                except Exception as api_err:
                    if attempt == max_retries - 1:
                        raise api_err
                    log.warning("gemini_api_retry", attempt=attempt+1, error=repr(api_err))
                    await asyncio.sleep(0.5 * (2 ** attempt))
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            try:
                # Strip markdown JSON fences if the LLM hallucinated them despite response_mime_type
                clean_text = re.sub(r'```json\n|\n```', '', response.text).strip()
                signals = json.loads(clean_text)
            except json.JSONDecodeError:
                signals = {}
                
            log.debug("signal_extracted", signals=signals, latency_ms=latency_ms)
            return {"signals": signals, "latency_ms": latency_ms}
            
        except Exception as e:
            log.error("signal_extraction_failed", error=repr(e))
            return {"signals": {}, "latency_ms": 0}
