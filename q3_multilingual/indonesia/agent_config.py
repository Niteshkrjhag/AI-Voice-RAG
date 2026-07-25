"""
q3_multilingual/indonesia/agent_config.py — ID Vapi Agent Configuration

Configures the Vapi assistant to use an Indonesian-capable TTS model
and the local system prompt for the Indonesia multifinance market.
"""

from typing import Dict, Any

from shared.config import config
from q1_voice_agent.tools import get_kb_search_tool_schema, get_schedule_callback_tool_schema
from q3_multilingual.indonesia.system_prompt import SYSTEM_PROMPT_ID, INITIAL_MESSAGE_ID

def get_indonesia_agent_config(public_api_url: str) -> Dict[str, Any]:
    return {
        "name": "ID Multifinance Bot",
        "firstMessage": INITIAL_MESSAGE_ID,
        "model": {
            "provider": "google",
            "model": "gemini-3.5-flash", # Multilingual strength
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT_ID
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
            "language": "multi" # Use 'multi' for Bahasa Indonesia ASR per Vapi schema
        }
    }
