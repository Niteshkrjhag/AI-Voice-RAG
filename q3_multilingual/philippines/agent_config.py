"""
q3_multilingual/philippines/agent_config.py — PH Vapi Agent Configuration

Configures the Vapi assistant to use a Taglish-capable TTS model
and the local system prompt for the Philippines market.
"""

from typing import Dict, Any

from shared.config import config
from q3_multilingual.philippines.system_prompt import SYSTEM_PROMPT_PH, INITIAL_MESSAGE_PH

def get_philippines_agent_config() -> Dict[str, Any]:
    return {
        "name": "PH Bancassurance Bot",
        "firstMessage": INITIAL_MESSAGE_PH,
        "model": {
            "provider": "google",
            "model": "gemini-2.0-flash", # Multilingual strength
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT_PH
                }
            ],
            "temperature": 0.5
        },
        "voice": {
            # Using 11labs or a provider with good Tagalog/English mix
            "provider": "11labs",
            "voiceId": "eleven_multilingual_v2", # Must support Tagalog
            "settings": {
                "stability": 0.6,
                "similarityBoost": 0.7
            }
        },
        "transcriber": {
            "provider": "assembly-ai",
            "language": "tl" # Tagalog ASR
        }
    }
