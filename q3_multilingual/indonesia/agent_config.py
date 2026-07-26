"""
q3_multilingual/indonesia/agent_config.py — ID Vapi Agent Configuration

Configures the Vapi assistant to use an Indonesian-capable TTS model
and the local system prompt for the Indonesia multifinance market.
"""

from typing import Dict, Any

from shared.config import config
from q1_voice_agent.tools import get_kb_search_tool_schema, get_schedule_callback_tool_schema, get_auth_tool_schema
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
            # Wire up the RAG Knowledge Base to the multilingual agent
            "tools": [
                get_kb_search_tool_schema(
                    api_url=public_api_url, 
                    rag_api_key=config.RAG_API_KEY, 
                    msg_start="Tunggu sebentar, saya periksa dokumen kebijakan kami...", 
                    msg_fail="Mohon maaf, ada gangguan pada sistem kami."
                ),
                get_schedule_callback_tool_schema(
                    api_url=public_api_url, 
                    rag_api_key=config.RAG_API_KEY,
                    msg_start="Saya akan menjadwalkan panggilan kembali untuk Anda.",
                    msg_fail="Mohon maaf, sistem penjadwalan tidak dapat diakses."
                ),
                get_auth_tool_schema(
                    api_url=public_api_url, 
                    rag_api_key=config.RAG_API_KEY,
                    msg_start="Saya akan memverifikasi detail Anda terlebih dahulu.",
                    msg_fail="Mohon maaf, saya tidak dapat memverifikasi detail tersebut."
                ),
                {"type": "transferCall", "destinations": [{"type": "number", "number": config.ID_TRANSFER_NUMBER, "message": "Mohon ditunggu, saya transfer ke manager."}]},
                {"type": "endCall"}
            ],
            "temperature": 0.5
        },
        "transcriber": {
            "provider": "assembly-ai",
            "language": "multi" # Use 'multi' for Bahasa Indonesia ASR per Vapi schema
        },
        "voice": {
            "provider": "azure",
            "voiceId": "id-ID-ArdiNeural"
        },
        "maxDurationSeconds": 1800
    }
