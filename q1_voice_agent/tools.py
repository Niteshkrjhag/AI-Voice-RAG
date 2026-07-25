"""
q1_voice_agent/tools.py — Custom tool definitions for the voice agent.

Defines the JSON Schema for the tools the LLM can call.
In Vapi (2026 API), these are passed in the `tools` array of the agent configuration.
"""

from typing import Dict, Any

def get_kb_search_tool_schema(api_url: str, rag_api_key: str) -> Dict[str, Any]:
    """
    Returns the Vapi-compatible tool schema for the Knowledge Base Search.
    This tells the LLM how and when to call our custom FastAPI endpoint.
    
    Args:
        api_url: The public URL where q2_knowledge_base/api.py is hosted.
        rag_api_key: The secret key for authenticating with the RAG backend.
    """
    return {
        "type": "apiRequest",
        "url": f"{api_url}/q2/api/v1/search",
        "method": "POST",
        "server": {
            "headers": {
                "Content-Type": "application/json",
                # SDE-3: Remove hardcoded InfoSec vulnerability. Inject from environment.
                "X-API-Key": rag_api_key
            }
        },
        "async": False,
        "messages": [
            {
                "type": "request-start",
                "content": "Let me quickly check our policy documents for that..."
            },
            {
                "type": "request-complete",
                "content": ""  # Handled dynamically by the LLM based on response
            },
            {
                "type": "request-failed",
                "content": "I'm having trouble accessing our system right now."
            }
        ],
        "function": {
            "name": "search_knowledge_base",
            "description": "Searches the Health Shield official knowledge base for answers regarding policies, coverage, waiting periods, and rules. Call this whenever the user asks a factual question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The specific question or search term (e.g., 'What is the waiting period for pre-existing diseases?')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results to return (default is 1)",
                        "default": 1
                    }
                },
                "required": ["query"]
            }
        }
    }

def get_schedule_callback_tool_schema(api_url: str) -> Dict[str, Any]:
    """
    Returns the tool schema for scheduling a callback (Optional Business Action).
    """
    return {
        "type": "apiRequest",
        "url": f"{api_url}/q1/api/v1/schedule_callback",
        "method": "POST",
        "server": {
            "headers": {
                "Content-Type": "application/json"
            }
        },
        "async": False,
        "messages": [
            {
                "type": "request-start",
                "content": "Let me pull up the calendar and schedule that callback for you."
            },
            {
                "type": "request-complete",
                "content": ""
            },
            {
                "type": "request-failed",
                "content": "I couldn't reach the scheduling system right now, but a senior agent will still reach out."
            }
        ],
        "function": {
            "name": "schedule_callback",
            "description": "Schedules a callback for a senior agent. Use this when the user is qualified and wants to proceed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "preferred_time": {
                        "type": "string",
                        "description": "The preferred time for the callback (e.g. 'tomorrow morning', '3 PM')"
                    },
                    "phone_number": {
                        "type": "string",
                        "description": "The customer's phone number to call back."
                    }
                },
                "required": ["preferred_time"]
            }
        }
    }
