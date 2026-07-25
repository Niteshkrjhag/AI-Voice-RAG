"""
q2_knowledge_base/embedder.py — Vector embedding and Qdrant indexing

Generates embeddings using OpenAI and indexes them into Qdrant.
Conforms to the 2026 qdrant-client v1.18.0 API.
"""

from typing import List
from openai import AsyncOpenAI
from qdrant_client import QdrantClient, models

from shared.config import config
from shared.logger import get_logger
from q2_knowledge_base.schema import KBRecord

log = get_logger("q2.embedder")

# Initialize clients using centralized config
openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
qdrant_client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)


async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate dense vector representations using OpenAI's embedding model.
    """
    if not texts:
        return []

    try:
        response = await openai_client.embeddings.create(
            input=texts,
            model=config.EMBEDDING_MODEL,
        )
        # Extract the embeddings from the response in order
        embeddings = [data.embedding for data in sorted(response.data, key=lambda x: x.index)]
        log.debug("embeddings_generated", count=len(embeddings))
        return embeddings
    except Exception as e:
        log.error("embedding_generation_failed", error=str(e))
        raise


def init_qdrant_collection():
    """
    Initialize the Qdrant collection if it doesn't exist.
    Configured for OpenAI's text-embedding-3-small (1536 dimensions).
    """
    collection_name = config.QDRANT_COLLECTION_NAME

    if not qdrant_client.collection_exists(collection_name=collection_name):
        log.info("creating_qdrant_collection", collection=collection_name)
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=1536,  # Specific to text-embedding-3-small
                distance=models.Distance.COSINE
            ),
        )
    else:
        log.debug("qdrant_collection_exists", collection=collection_name)


async def index_records(records: List[KBRecord]):
    """
    Generate embeddings for records and index them into Qdrant.

    Args:
        records: List of KBRecords (from chunker)
    """
    if not records:
        return

    # Ensure collection exists before inserting
    init_qdrant_collection()

    # Extract texts for embedding
    texts = [record.content for record in records]
    embeddings = await generate_embeddings(texts)

    # Prepare Qdrant point structures
    points = []
    for record, vector in zip(records, embeddings):
        # Qdrant expects payload to be a dict, so we dump the Pydantic model
        payload = record.model_dump(mode='json')

        points.append(
            models.PointStruct(
                id=record.id,  # Ensure UUID or stable string hash
                vector=vector,
                payload=payload
            )
        )

    # Upsert points into Qdrant
    qdrant_client.upsert(
        collection_name=config.QDRANT_COLLECTION_NAME,
        points=points
    )
    log.info("records_indexed", count=len(points), collection=config.QDRANT_COLLECTION_NAME)
