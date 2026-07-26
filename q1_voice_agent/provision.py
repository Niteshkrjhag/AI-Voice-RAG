"""
q1_voice_agent/provision.py — Provisions the Vapi agent via REST API.

Registers our Assistant configuration with Vapi and returns the Assistant ID,
which can then be used in a Web SDK frontend.
"""

import os
import requests

from shared.config import config
from shared.logger import get_logger
from q1_voice_agent.agent_config import get_vapi_agent_config

log = get_logger("q1.provision")

VAPI_BASE_URL = "https://api.vapi.ai"

def provision_assistant():
    """
    Creates or updates the Voice Agent on Vapi using our configuration.
    """
    api_key = config.VAPI_API_KEY
    if not api_key:
        log.error("vapi_api_key_missing")
        print("Error: VAPI_API_KEY is not set in .env")
        return

    # In a real environment, you would use ngrok to expose your local FastAPI server.
    # For this provision script, we assume a placeholder or require the user to pass it.
    public_api_url = os.getenv("NGROK_URL", "https://your-ngrok-url.ngrok.app")
    if "your-ngrok-url" in public_api_url:
        log.warning("using_placeholder_ngrok_url")
        print("WARNING: Using placeholder NGROK_URL. Your agent won't be able to reach your local FastAPI server.")
        print("Run `ngrok http 8000`, then set `export NGROK_URL=https://...` before running this script.")
        
    assistant_config = get_vapi_agent_config(public_api_url)

    from shared.vapi_client import provision_assistant as shared_provision
    shared_provision(assistant_config)


if __name__ == "__main__":
    provision_assistant()
