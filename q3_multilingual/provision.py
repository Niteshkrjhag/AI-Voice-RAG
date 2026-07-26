"""
q3_multilingual/provision.py — Provisions the Multilingual Vapi agents.

Reuses the idempotent provisioning logic from Q1, but applies the
Philippines or Indonesia configuration based on CLI arguments.
"""

import os
import sys
import requests

from shared.config import config
from shared.logger import get_logger
from q3_multilingual.philippines.agent_config import get_philippines_agent_config
from q3_multilingual.indonesia.agent_config import get_indonesia_agent_config

log = get_logger("q3.provision")

VAPI_BASE_URL = "https://api.vapi.ai"

def provision_multilingual_assistant(market: str):
    """
    Creates or updates the Voice Agent on Vapi for the specified market.
    """
    api_key = config.VAPI_API_KEY
    if not api_key:
        log.error("vapi_api_key_missing")
        print("Error: VAPI_API_KEY is not set in .env")
        return

    public_api_url = os.getenv("NGROK_URL", "https://your-ngrok-url.ngrok.app")
    if "your-ngrok-url" in public_api_url:
        log.warning("using_placeholder_ngrok_url")
        print("WARNING: Using placeholder NGROK_URL. Your agent won't be able to reach your local FastAPI server.")
        print("Run `ngrok http 8000`, then set `export NGROK_URL=https://...` before running this script.")
        
    if market.lower() == "ph":
        assistant_config = get_philippines_agent_config(public_api_url)
    elif market.lower() == "id":
        assistant_config = get_indonesia_agent_config(public_api_url)
    else:
        print("Error: Unknown market. Use 'ph' for Philippines or 'id' for Indonesia.")
        sys.exit(1)

    from shared.vapi_client import provision_assistant
    provision_assistant(assistant_config, market=market)


if __name__ == "__main__":
    market = sys.argv[1] if len(sys.argv) > 1 else None
    if not market:
        print("Usage: python -m q3_multilingual.provision [ph|id]")
        sys.exit(1)
    provision_multilingual_assistant(market)
