"""
q1_voice_agent/tools.py — Custom tool definitions for the voice agent.

Defines the JSON Schema for the tools the LLM can call.
In Vapi (2026 API), these are passed in the `tools` array of the agent configuration.
"""

from typing import Dict, Any

def get_kb_search_tool_schema(api_url: str, rag_api_key: str, msg_start: str = "Let me quickly check our policy documents for that...", msg_fail: str = "I'm having trouble accessing our system right now.") -> Dict[str, Any]:
    """
    Returns the Vapi-compatible tool schema for the Knowledge Base Search.
    This tells the LLM how and when to call our custom FastAPI endpoint.
    
    Args:
        api_url: The public URL where q2_knowledge_base/api.py is hosted.
        rag_api_key: The secret key for authenticating with the RAG backend.
        msg_start: Localized message to say before starting the request.
        msg_fail: Localized message to say if the request fails.
    """
    return {
        "type": "apiRequest",
        "url": f"{api_url}/q2/api/v1/search?api_key={rag_api_key}",
        "method": "POST",
        "async": False,
        "server": {
            "url": f"{api_url}/q2/api/v1/search?api_key={rag_api_key}"
        },
        "messages": [
            {
                "type": "request-start",
                "content": msg_start
            },
            {
                "type": "request-complete",
                "content": ""  # Handled dynamically by the LLM based on response
            },
            {
                "type": "request-failed",
                "content": msg_fail
            }
        ],
        "function": {
            "name": "search_knowledge_base",
            "description": "CRITICAL: You MUST provide the 'query' parameter with the user's exact question. Searches the Health Shield official knowledge base for answers regarding policies, coverage, waiting periods, and rules.",
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

def get_schedule_callback_tool_schema(api_url: str, rag_api_key: str, msg_start: str = "Let me pull up the calendar and schedule that callback for you.", msg_fail: str = "I couldn't reach the scheduling system right now, but a senior agent will still reach out.") -> Dict[str, Any]:
    """
    Returns the tool schema for scheduling a callback (Optional Business Action).
    """
    return {
        "type": "apiRequest",
        "url": f"{api_url}/q1/api/v1/schedule_callback?api_key={rag_api_key}",
        "method": "POST",
        "async": False,
        "server": {
            "url": f"{api_url}/q1/api/v1/schedule_callback?api_key={rag_api_key}"
        },
        "messages": [
            {
                "type": "request-start",
                "content": msg_start
            },
            {
                "type": "request-complete",
                "content": ""
            },
            {
                "type": "request-failed",
                "content": msg_fail
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

def get_auth_tool_schema(api_url: str, rag_api_key: str, msg_start: str = "Let me verify those details in our system.", msg_fail: str = "I couldn't verify those details right now.") -> Dict[str, Any]:
    """
    Returns the tool schema for authenticating a caller to prevent PII leakage.
    """
    return {
        "type": "apiRequest",
        "url": f"{api_url}/q1/api/v1/authenticate?api_key={rag_api_key}",
        "method": "POST",
        "async": False,
        "server": {
            "url": f"{api_url}/q1/api/v1/authenticate?api_key={rag_api_key}"
        },
        "messages": [
            {
                "type": "request-start",
                "content": msg_start
            },
            {
                "type": "request-complete",
                "content": ""
            },
            {
                "type": "request-failed",
                "content": msg_fail
            }
        ],
        "function": {
            "name": "authenticate_caller",
            "description": "Authenticates the caller before releasing any sensitive PII or policy details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dob": {
                        "type": "string",
                        "description": "The customer's date of birth (e.g. 1990-05-12)."
                    },
                    "policy_number": {
                        "type": "string",
                        "description": "The customer's policy number."
                    }
                },
                "required": ["dob", "policy_number"]
            }
        }
    }
