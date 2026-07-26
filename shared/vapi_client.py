import requests
import sys
from typing import Dict, Any, Optional

from shared.config import config
from shared.logger import get_logger

log = get_logger("vapi_client")
VAPI_BASE_URL = "https://api.vapi.ai"

def provision_assistant(assistant_config: Dict[str, Any], market: Optional[str] = None) -> None:
    """
    Creates or updates a Voice Agent on Vapi idempotently based on the assistant name.
    """
    api_key = config.VAPI_API_KEY
    if not api_key:
        log.error("vapi_api_key_missing")
        print("Error: VAPI_API_KEY is not set in .env")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        # Fetch existing assistants to prevent duplicating bots (Idempotency)
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
        log_ctx = {"assistant_id": assistant_id}
        if market:
            log_ctx["market"] = market
            
        log.info("vapi_assistant_ready", **log_ctx)
        
        market_label = f" {market.upper()}" if market else ""
        print(f"✅ Successfully {action_verb}{market_label} Vapi Assistant!")
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
        sys.exit(1)
