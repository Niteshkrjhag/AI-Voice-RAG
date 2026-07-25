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
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        # SDE-3: Fetch existing assistants to prevent duplicating bots (Idempotency)
        get_resp = requests.get(f"{VAPI_BASE_URL}/assistant", headers=headers)
        get_resp.raise_for_status()
        
        existing_assistants = get_resp.json()
        target_assistant_id = None
        for agent in existing_assistants:
            if agent.get("name") == assistant_config.get("name"):
                target_assistant_id = agent.get("id")
                break
                
        if target_assistant_id:
            log.info("updating_existing_vapi_assistant", assistant_id=target_assistant_id)
            response = requests.patch(f"{VAPI_BASE_URL}/assistant/{target_assistant_id}", headers=headers, json=assistant_config)
            action_verb = "updated"
        else:
            log.info("creating_new_vapi_assistant")
            response = requests.post(f"{VAPI_BASE_URL}/assistant", headers=headers, json=assistant_config)
            action_verb = "provisioned"
            
        response.raise_for_status()

        data = response.json()
        assistant_id = data.get("id")
        log.info("vapi_assistant_ready", market=market, assistant_id=assistant_id)
        print(f"✅ Successfully {action_verb} {market.upper()} Vapi Assistant!")
        print(f"Assistant ID: {assistant_id}")
        print("\nNext Steps:")
        print("1. Start your local KB FastAPI server: `python -m uvicorn q2_knowledge_base.api:app --port 8000`")
        print("2. Ensure ngrok is forwarding to port 8000.")
        print("3. Use this Assistant ID in your Vapi Web SDK to start a call.")
        
    except requests.exceptions.RequestException as e:
        log.error("vapi_provisioning_failed", error=str(e))
        print(f"❌ Failed to provision/update assistant. Network error or bad response: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Details: {e.response.text}")


if __name__ == "__main__":
    market = sys.argv[1] if len(sys.argv) > 1 else None
    if not market:
        print("Usage: python -m q3_multilingual.provision [ph|id]")
        sys.exit(1)
    provision_multilingual_assistant(market)
