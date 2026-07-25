"""
q3_multilingual/indonesia/agent_config.py — ID Vapi Agent Configuration

Configures the Vapi assistant to use an Indonesian-capable TTS model
and the local system prompt for the Indonesia multifinance market.
"""

from typing import Dict, Any

from shared.config import config
from q3_multilingual.indonesia.system_prompt import SYSTEM_PROMPT_ID, INITIAL_MESSAGE_ID

def get_indonesia_agent_config() -> Dict[str, Any]:
    return {
        "name": "ID Multifinance Bot",
        "firstMessage": INITIAL_MESSAGE_ID,
        "model": {
            "provider": "google",
            "model": "gemini-2.0-flash",
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT_ID
                }
            ],
            "temperature": 0.5
        },
        "voice": {
            # SDE-3: Fixed invalid model string in voiceId. Must use actual character hash.
            "provider": "11labs",
            "voiceId": "21m00Tcm4TlvDq8ikWAM", # Rachel voice hash
            "model": "eleven_multilingual_v2", # Must support Bahasa Indonesia
            "settings": {
                "stability": 0.6,
                "similarityBoost": 0.7
            }
        },
        "transcriber": {
            "provider": "assembly-ai",
            "language": "id" # Bahasa Indonesia ASR
        }
    }
