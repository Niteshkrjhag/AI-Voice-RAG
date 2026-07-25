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
            # Check suppression window
            last_time = self._last_nudge_times.get(signal_type, 0)
            if current_time_ms - last_time < self.suppression_window_ms:
                log.debug("nudge_suppressed", signal_type=signal_type)
                continue

            # Generate nudge based on signal type
            nudge = self._generate_nudge(signal_type, details)
            if nudge:
                nudges.append(nudge)
                self._last_nudge_times[signal_type] = current_time_ms
                log.info("nudge_generated", type=signal_type, content=nudge)

        return nudges

    def _generate_nudge(self, signal_type: str, details: any) -> dict:
        if signal_type == "missed_cross_sell":
            return {
                "type": "SUGGESTION",
                "message": "Customer mentioned family. Offer the Family Floater rider.",
                "urgency": "low"
            }
        elif signal_type == "compliance_gap":
            return {
                "type": "COMPLIANCE",
                "message": "⚠️ You must mention the 30-day waiting period for new illnesses.",
                "urgency": "high"
            }
        elif signal_type == "frustration":
            return {
                "type": "ALERT",
                "message": "🚨 Customer sounds frustrated. Empathize and offer senior callback.",
                "urgency": "high"
            }
        return None
