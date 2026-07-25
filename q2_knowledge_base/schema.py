"""
q2_knowledge_base/schema.py — Knowledge Base Record Schema

Defines the canonical data structure for every record in the knowledge base.
All modules (scraper, cleaner, chunker, embedder, retriever) operate on
this schema. The schema is designed to satisfy the assessment's traceability
requirement: every answer must link back to a source, version, and category.

Field reference from assessment:
  record_id, title, content, category, source, version, pii_flag
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from uuid import uuid4


class KBRecord(BaseModel):
    """
    A single knowledge base record.

    This is the atomic unit of the KB — one chunk of information with
    full provenance metadata for citation and traceability.
    """

    # ── Identity ────────────────────────────────────────────────
    # UUID v4 with descriptive prefix for human readability
    record_id: str = Field(
        default_factory=lambda: f"kb_{uuid4().hex[:12]}",
        description="Unique identifier for this KB record"
    )

    # ── Content ─────────────────────────────────────────────────
    title: str = Field(
        ...,
        description="Descriptive title summarizing the chunk content"
    )
    content: str = Field(
        ...,
        description="The actual text content of this knowledge chunk"
    )

    # ── Taxonomy & Classification ───────────────────────────────
    # Category uses a product/policy taxonomy for structured retrieval
    category: str = Field(
        ...,
        description=(
            "Hierarchical category. Values: product_info, policy_rules, "
            "eligibility_criteria, faq, objection_handling, pricing, "
            "claims_process, partnership_benefits, compliance"
        )
    )

    # ── Source Tracking ─────────────────────────────────────────
    # Every record must trace back to its origin for citation
    source: str = Field(
        ...,
        description="Origin of this content (e.g., 'website/products', 'pdf/policy_doc')"
    )
    source_url: Optional[str] = Field(
        default=None,
        description="Original URL if scraped from web"
    )

    # ── Versioning ──────────────────────────────────────────────
    version: str = Field(
        default="1.0",
        description="Content version for change tracking"
    )

    # ── PII Flag ────────────────────────────────────────────────
    # Assessment requires PII identification and protection
    pii_detected: bool = Field(
        default=False,
        description="Whether PII was detected and anonymized in this record"
    )

    # ── Metadata ────────────────────────────────────────────────
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO 8601 timestamp of record creation"
    )
    chunk_index: int = Field(
        default=0,
        description="Position of this chunk within the parent document"
    )
    parent_doc_id: Optional[str] = Field(
        default=None,
        description="ID of the parent document this chunk was extracted from"
    )
    token_count: int = Field(
        default=0,
        description="Number of tokens in the content field"
    )

    class Config:
        # Allow serialization to JSON for storage and transport
        json_schema_extra = {
            "example": {
                "record_id": "kb_a1b2c3d4e5f6",
                "title": "Individual Health Plan - Coverage Details",
                "content": "The individual health plan covers hospitalization expenses...",
                "category": "product_info",
                "source": "website/products/individual-plan",
                "source_url": "https://example.com/products/individual-plan",
                "version": "1.0",
                "pii_detected": False,
                "created_at": "2026-07-25T10:00:00",
                "chunk_index": 0,
                "parent_doc_id": "doc_abc123",
                "token_count": 245,
            }
        }


class RetrievalResult(BaseModel):
    """
    A single retrieval result returned by the KB search endpoint.
    Includes the matched record plus relevance scoring for evaluation.
    """

    record: KBRecord = Field(
        ...,
        description="The matched knowledge base record"
    )
    relevance_score: float = Field(
        ...,
        description="Cosine similarity score from vector search (0.0 to 1.0)"
    )
    rank: int = Field(
        ...,
        description="Position in the result set (1-indexed)"
    )


class RetrievalRequest(BaseModel):
    """
    Incoming search request to the KB retrieval API.
    Used by the voice agent's tool call and the test harness.
    """

    query: str = Field(
        ...,
        description="Natural language search query"
    )
    top_k: int = Field(
        default=5,
        description="Number of top results to return"
    )
    category_filter: Optional[str] = Field(
        default=None,
        description="Optional category filter to narrow search scope"
    )


class RetrievalResponse(BaseModel):
    """
    Response from the KB retrieval API.
    Contains matched records with scores and the original query for tracing.
    """

    query: str = Field(
        ...,
        description="The original search query"
    )
    results: list[RetrievalResult] = Field(
        default_factory=list,
        description="Ranked list of matching KB records"
    )
    total_results: int = Field(
        default=0,
        description="Total number of results returned"
    )
