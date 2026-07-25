"""
q4_live_insights/nudge_engine.py — Nudge Generation and Suppression.

Processes the signals from the signal_extractor and generates UI nudges for the agent.
Implements suppression logic to avoid spamming the agent.
"""

import time
from shared.logger import get_logger

log = get_logger("q4.nudge_engine")


class NudgeEngine:
    def __init__(self, suppression_window_ms: int = 15000):
        # We suppress duplicate nudge types for a given window to prevent distraction
        self.suppression_window_ms = suppression_window_ms
        self._last_nudge_times = {}

    def process_signals(self, signals: dict) -> list[dict]:
        """
        Takes raw signals from the LLM and generates actionable nudges.
        """
        nudges = []
        current_time_ms = int(time.time() * 1000)

        for signal_type, details in signals.items():
            # False Positive Control: Check confidence threshold
            confidence = details.get("confidence_score", 0) if isinstance(details, dict) else 100
            if confidence < 75:
                log.debug("nudge_suppressed_low_confidence", signal_type=signal_type, confidence=confidence)
                continue

            # Check suppression window
            last_time = self._last_nudge_times.get(signal_type, 0)
            if current_time_ms - last_time < self.suppression_window_ms:
                log.debug("nudge_suppressed_cooldown", signal_type=signal_type)
                continue

            # Generate nudge based on signal type
            nudge = self._generate_nudge(signal_type, details)
            if nudge:
                nudges.append(nudge)
                self._last_nudge_times[signal_type] = current_time_ms
                log.info("nudge_generated", type=signal_type, content=nudge)

        return nudges

    def _generate_nudge(self, signal_type: str, details: any) -> dict:
        # Extract the dynamic text provided by the LLM if it's a dict, or fallback to string
        dynamic_message = details if isinstance(details, str) else str(details.get("reasoning", details))
        
        if signal_type == "missed_cross_sell":
            return {
                "type": "SUGGESTION",
                "message": f"Cross-sell Opportunity: {dynamic_message}",
                "urgency": "low"
            }
        elif signal_type == "compliance_gap":
            return {
                "type": "COMPLIANCE",
                "message": f"⚠️ Compliance Risk: {dynamic_message}",
                "urgency": "high"
            }
        elif signal_type == "frustration":
            return {
                "type": "ALERT",
                "message": f"🚨 Frustration Detected: {dynamic_message}",
                "urgency": "high"
            }
        return None
