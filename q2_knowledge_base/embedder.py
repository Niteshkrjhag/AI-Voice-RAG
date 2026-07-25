"""
q2_knowledge_base/embedder.py — Vector embedding and Qdrant indexing

Generates embeddings using OpenAI and indexes them into Qdrant.
Conforms to the 2026 qdrant-client v1.18.0 API.
"""

from typing import List

from qdrant_client import QdrantClient, models

from shared.config import config
from shared.logger import get_logger
from q2_knowledge_base.schema import KBRecord

from sentence_transformers import SentenceTransformer

log = get_logger("q2.embedder")

# Initialize clients using centralized config
# Load the local sentence-transformer model in memory
embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
qdrant_client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate dense vector representations using the local SentenceTransformers model.
    """
    if not texts:
        return []

    try:
        # encode() returns a numpy array, we convert to list of floats for Qdrant
        embeddings = embedding_model.encode(texts, show_progress_bar=False)
        embeddings_list = [vector.tolist() for vector in embeddings]
        log.debug("embeddings_generated", count=len(embeddings_list))
        return embeddings_list
    except Exception as e:
        log.error("embedding_generation_failed", error=str(e))
        raise


def init_qdrant_collection():
    """
    Initialize the Qdrant collection if it doesn't exist.
    Configured for the configured dimension size (e.g. 384 for all-MiniLM-L6-v2).
    """
    collection_name = config.QDRANT_COLLECTION_NAME

    if not qdrant_client.collection_exists(collection_name=collection_name):
        log.info("creating_qdrant_collection", collection=collection_name)
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=config.EMBEDDING_DIMENSIONS,
                distance=models.Distance.COSINE
            ),
        )
    else:
        log.debug("qdrant_collection_exists", collection=collection_name)


def index_records(records: List[KBRecord]):
    """
    Generate embeddings for records and index them into Qdrant.

    Args:
        records: List of KBRecords (from chunker)
    """
    if not records:
        return

    # Ensure collection exists before inserting
    init_qdrant_collection()
    
    BATCH_SIZE = 32
    
    # SDE-3: Process in batches to prevent Out-Of-Memory (OOM) crashes on large doc sets
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        
        # Extract texts for embedding
        texts = [record.content for record in batch]
        embeddings = generate_embeddings(texts)
    
        # Prepare Qdrant point structures
        points = []
        for record, vector in zip(batch, embeddings):
            # Qdrant expects payload to be a dict, so we dump the Pydantic model
            payload = record.model_dump(mode='json')
    
            points.append(
                models.PointStruct(
                    id=record.record_id,  # Ensure UUID or stable string hash
                    vector=vector,
                    payload=payload
                )
            )
    
        try:
            # Upload the vectors and payloads to Qdrant
            qdrant_client.upsert(
                collection_name=config.QDRANT_COLLECTION_NAME,
                points=points
            )
            log.info("batch_indexed", collection=config.QDRANT_COLLECTION_NAME, size=len(points))
        except Exception as e:
            log.error("qdrant_batch_upsert_failed", error=str(e), collection=config.QDRANT_COLLECTION_NAME)
            # We don't raise here to allow the pipeline to continue or gracefully exit
            print(f"❌ Failed to push batch to Qdrant: {e}")
            
    log.info("all_records_indexed", total=len(records))
