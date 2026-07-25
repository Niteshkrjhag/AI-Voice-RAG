"""
q2_knowledge_base/api.py — FastAPI endpoints for knowledge retrieval

Exposes the knowledge base to external voice agents (e.g., Vapi tools).
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List

from shared.logger import get_logger
from q2_knowledge_base.retriever import search_knowledge_base
from q2_knowledge_base.schema import KBRecord

log = get_logger("q2.api")

app = FastAPI(
    title="Production Voice AI Knowledge Base API",
    description="RAG retrieval endpoints for voice agents.",
    version="1.0.0",
)


class SearchRequest(BaseModel):
    query: str
    limit: int = 5


class SearchResponse(BaseModel):
    results: List[KBRecord]


@app.post("/api/v1/search", response_model=SearchResponse)
async def search_kb(request: SearchRequest):
    """
    Search the knowledge base for relevant documents.
    Intended to be called as a custom tool by the voice agent (e.g., Vapi).
    """
    log.info("search_request_received", query=request.query, limit=request.limit)
    
    try:
        records = await search_knowledge_base(query=request.query, limit=request.limit)
        return SearchResponse(results=records)
    except Exception as e:
        log.error("search_endpoint_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error during search.")


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}
