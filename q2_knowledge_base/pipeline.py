"""
q2_knowledge_base/pipeline.py — Orchestrates the full KB ingestion pipeline.

Pipeline Steps:
1. Load raw scraped JSON files
2. Clean and deduplicate content
3. Chunk into semantic segments
4. Embed and index into Qdrant
"""

import json
import asyncio
from pathlib import Path

from shared.config import config
from shared.logger import get_logger
from q2_knowledge_base.cleaner import clean_document, deduplicate
from q2_knowledge_base.chunker import chunk_documents
from q2_knowledge_base.embedder import index_records

log = get_logger("q2.pipeline")


async def run_pipeline():
    log.info("kb_pipeline_started")
    raw_dir = config.DATA_RAW_DIR
    
    if not raw_dir.exists():
        log.error("raw_directory_missing", path=str(raw_dir))
        return

    # 1. Load raw documents
    raw_docs = []
    for filepath in raw_dir.glob("*.json"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw_docs.append(json.load(f))
        except Exception as e:
            log.error("failed_to_load_raw_doc", file=filepath.name, error=str(e))

    log.info("documents_loaded", count=len(raw_docs))

    # 2. Clean documents
    cleaned_docs = []
    for doc in raw_docs:
        cleaned = clean_document(doc)
        if cleaned:
            cleaned_docs.append(cleaned)
            
    # 3. Deduplicate (removes near-duplicates based on content hash)
    unique_docs = deduplicate(cleaned_docs, content_key="content")
    
    # Save cleaned documents for traceability
    cleaned_dir = config.DATA_DIR / "cleaned"
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    for doc in unique_docs:
        safe_name = f"doc_{doc['content_hash'][:8]}.json"
        with open(cleaned_dir / safe_name, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)

    log.info("documents_cleaned_and_deduplicated", unique_count=len(unique_docs))

    # 4. Chunk documents
    records = chunk_documents(unique_docs)
    
    # 5. Embed and Index
    await index_records(records)
    
    log.info("kb_pipeline_completed", total_records_indexed=len(records))


if __name__ == "__main__":
    asyncio.run(run_pipeline())
