"""
q1_voice_agent/agent_config.py — Vapi agent configuration structure.

Defines the payload required to create or update the voice agent via Vapi's REST API.
"""

from typing import Dict, Any

from shared.config import config
from q1_voice_agent.system_prompt import SYSTEM_PROMPT, INITIAL_MESSAGE
from q1_voice_agent.tools import get_kb_search_tool_schema


def get_vapi_agent_config(public_api_url: str) -> Dict[str, Any]:
    """
    Constructs the Vapi Assistant configuration object.
    
    Args:
        public_api_url: The public URL (e.g., ngrok) where our FastAPI server is exposed.
    """
    
    # 2026 Vapi Assistant Configuration Schema
    return {
        "name": "Health Shield RAG Agent",
        "firstMessage": INITIAL_MESSAGE,
        "model": {
            "provider": "google",
            "model": "gemini-3.5-flash",
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                }
            ],
            "tools": [
                get_kb_search_tool_schema(api_url=public_api_url, rag_api_key=config.RAG_API_KEY)
            ],
            "temperature": 0.4  # Lower temp to reduce hallucination risk
        },
        "transcriber": {
            "provider": "assembly-ai",
            "language": "en"
        },
        "recordingEnabled": True,  # Required for assessment (must record test calls)
        "endCallFunctionEnabled": True,
        "clientMessages": [
            "transcript",
            "hang",
            "function-call",
            "speech-update"
        ]
    }

