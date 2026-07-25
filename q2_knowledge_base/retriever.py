"""
q2_knowledge_base/retriever.py — Semantic search and RAG retrieval logic

Queries Qdrant to find relevant knowledge base records.
"""

from typing import List

from shared.config import config
from shared.logger import get_logger
from q2_knowledge_base.schema import KBRecord
from q2_knowledge_base.embedder import generate_embeddings, qdrant_client

log = get_logger("q2.retriever")


async def search_knowledge_base(query: str, limit: int = 5) -> List[KBRecord]:
    """
    Search the vector database for records matching the query.

    Args:
        query: The user's question or search term
        limit: Max number of records to return

    Returns:
        List of KBRecords ordered by relevance score.
    """
    # 1. Embed the search query
    try:
        query_embeddings = generate_embeddings([query])
        query_vector = query_embeddings[0]
    except Exception as e:
        log.error("query_embedding_failed", query=query, error=str(e))
        return []

    # 2. Search Qdrant
    try:
        search_results = qdrant_client.query_points(
            collection_name=config.QDRANT_COLLECTION_NAME,
            query=query_vector,
            limit=limit,
        ).points
    except Exception as e:
        log.error("qdrant_search_failed", query=query, error=str(e))
        return []

    # 3. Reconstruct KBRecords from payload
    records = []
    for hit in search_results:
        # hit.payload contains the dumped JSON of the Pydantic model
        if hit.payload:
            try:
                # Add score for transparency (not strictly in KBRecord schema but useful for debugging)
                record = KBRecord.model_validate(hit.payload)
                records.append(record)
                log.debug("search_hit", id=hit.id, score=hit.score, title=record.title)
            except Exception as e:
                log.warning("invalid_payload_in_qdrant", hit_id=hit.id, error=str(e))

    log.info("search_complete", query=query, results=len(records))
    return records
