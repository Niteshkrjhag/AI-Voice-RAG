"""
q3_multilingual/philippines/agent_config.py — PH Vapi Agent Configuration

Configures the Vapi assistant to use a Taglish-capable TTS model
and the local system prompt for the Philippines market.
"""

from typing import Dict, Any

from shared.config import config
from q1_voice_agent.tools import get_kb_search_tool_schema, get_schedule_callback_tool_schema
from q3_multilingual.philippines.system_prompt import SYSTEM_PROMPT_PH, INITIAL_MESSAGE_PH

def get_philippines_agent_config(public_api_url: str) -> Dict[str, Any]:
    return {
        "name": "PH Bancassurance Bot",
        "firstMessage": INITIAL_MESSAGE_PH,
        "model": {
            "provider": "google",
            "model": "gemini-3.5-flash", # Multilingual strength
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT_PH
                }
            ],
            # SDE-3: Wire up the RAG Knowledge Base to the multilingual agent
            "tools": [
                get_kb_search_tool_schema(api_url=public_api_url, rag_api_key=config.RAG_API_KEY),
                get_schedule_callback_tool_schema(api_url=public_api_url)
            ],
            "temperature": 0.5
        },
        "transcriber": {
            "provider": "assembly-ai",
            "language": "multi" # Use 'multi' for Tagalog ASR per Vapi schema
        }
    }
