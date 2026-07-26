"""
q2_knowledge_base/api.py — FastAPI endpoints for knowledge retrieval

Exposes the knowledge base to external voice agents (e.g., Vapi tools).
"""

from fastapi import FastAPI, HTTPException, Query, Depends, Security, Request
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import traceback

from shared.config import config
from shared.logger import get_logger
from q2_knowledge_base.retriever import search_knowledge_base
from q2_knowledge_base.schema import KBRecord

log = get_logger("q2.api")

app = FastAPI(
    title="Production Voice AI Knowledge Base API",
    description="RAG retrieval endpoints for voice agents.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key Security
# Removed hardcoded API key fallback. Must be configured securely.
API_KEY = config.RAG_API_KEY
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
vapi_secret_header = APIKeyHeader(name="x-vapi-secret", auto_error=False)

async def get_api_key(
    request: Request,
    api_key_header: str = Security(api_key_header),
    vapi_secret: str = Security(vapi_secret_header),
    api_key: str = Query(None)
):
    log.info("auth_trace_start", message="Starting API Key validation")
    log.info("auth_trace_headers", headers=dict(request.headers))
    log.info("auth_trace_query", query=dict(request.query_params))
    log.info("auth_trace_extracted", api_key_header=api_key_header, vapi_secret=vapi_secret, query_api_key=api_key)
    log.info("auth_trace_expected", expected_key=API_KEY)
    
    if api_key_header == API_KEY:
        log.info("auth_trace_success", reason="Matched via X-API-Key header")
        return True
    if vapi_secret == API_KEY:
        log.info("auth_trace_success", reason="Matched via x-vapi-secret header")
        return True
    if api_key == API_KEY:
        log.info("auth_trace_success", reason="Matched via api_key query parameter")
        return True
            
    log.error("auth_trace_failed", message="No valid API key found in headers or query params")
    raise HTTPException(status_code=403, detail="Could not validate API KEY")


class SearchRequest(BaseModel):
    query: str
    limit: int = 5


class SearchResult(BaseModel):
    title: str
    content: str
    source_url: str

class SearchResponse(BaseModel):
    results: List[SearchResult]


@app.post("/api/v1/search")
async def search_kb(request: Request, api_key: str = Depends(get_api_key)):
    """
    Search the knowledge base for relevant documents.
    Intended to be called as a custom tool by the voice agent (e.g., Vapi).
    """
    try:
        body = await request.json()
        log.info("search_request_body", body=body)
            
        # Extract query
        query = None
        limit = 5
        
        if "query" in body:
            query = body["query"]
            limit = body.get("limit", 5)
        elif "message" in body and "toolWithToolCallList" in body["message"]:
            # Vapi nested webhook payload
            tool_call = body["message"]["toolWithToolCallList"][0]["toolCall"]
            args = tool_call["function"]["arguments"]
            # arguments might be a string (JSON) or a dict
            if isinstance(args, str):
                args = json.loads(args)
            query = args.get("query")
            limit = args.get("limit", 5)
        elif "message" in body and "toolCalls" in body["message"]:
            # Alternative Vapi structure
            tool_call = body["message"]["toolCalls"][0]
            args = tool_call["function"]["arguments"]
            if isinstance(args, str):
                args = json.loads(args)
            query = args.get("query")
            limit = args.get("limit", 5)
            
        if not query:
            log.warning("search_empty_query", body=body)
            # Graceful fallback for LLM hallucination (empty arguments)
            # Instead of crashing VAPI with an HTTP error, tell the LLM to ask the user.
            return {
                "results": [
                    {
                        "title": "System Instruction",
                        "content": "You called the search tool without providing a 'query' parameter. Please ask the user to clarify what specific information they are looking for.",
                        "source_url": "system"
                    }
                ]
            }
            
        log.info("search_request_extracted", query=query, limit=limit)
        
        records = await search_knowledge_base(query=query, limit=limit)
        # Flatten the KBRecords into a token-efficient response
        simplified = [
            SearchResult(title=r.title, content=r.content, source_url=r.source_url)
            for r in records
        ]
        
        # VAPI expects the response directly. We can just return the results array.
        return {"results": [s.dict() for s in simplified]}
    except HTTPException:
        # Re-raise HTTP exceptions so we don't mask them
        raise
    except Exception as e:
        err_msg = traceback.format_exc()
        log.error("search_endpoint_failed", error=str(e), trace=err_msg)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)} - {err_msg}")


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}
