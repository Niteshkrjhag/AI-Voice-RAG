"""
q2_knowledge_base/api.py — FastAPI endpoints for knowledge retrieval

Exposes the knowledge base to external voice agents (e.g., Vapi tools).
"""

from fastapi import FastAPI, HTTPException, Query, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import os

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
# SDE-3: Removed hardcoded API key fallback. Must be configured securely.
API_KEY = config.RAG_API_KEY
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
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


@app.post("/api/v1/search", response_model=SearchResponse)
async def search_kb(request: SearchRequest, api_key: str = Depends(get_api_key)):
    """
    Search the knowledge base for relevant documents.
    Intended to be called as a custom tool by the voice agent (e.g., Vapi).
    """
    log.info("search_request_received", query=request.query, limit=request.limit)
    
    try:
        records = await search_knowledge_base(query=request.query, limit=request.limit)
        # Flatten the KBRecords into a token-efficient response
        simplified = [
            SearchResult(title=r.title, content=r.content, source_url=r.source_url)
            for r in records
        ]
        return SearchResponse(results=simplified)
    except Exception as e:
        log.error("search_endpoint_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error during search.")


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}
