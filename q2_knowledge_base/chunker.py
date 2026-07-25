"""
q2_knowledge_base/chunker.py — Semantic chunking for RAG

Breaks cleaned text into manageable overlapping chunks.
Maintains traceability to the source document and preserves metadata.
"""

from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter

from shared.logger import get_logger
from q2_knowledge_base.schema import KBRecord

log = get_logger("q2.chunker")


def chunk_document(
    doc_id: str,
    title: str,
    content: str,
    source_url: str,
    pii_flags: bool,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[KBRecord]:
    """
    Split a cleaned document into semantic chunks using LangChain.

    Args:
        doc_id: Unique identifier for the source document
        title: Document title
        content: Cleaned document text
        source_url: Original URL for traceability
        pii_flags: Whether the original text contained PII
        chunk_size: Target size of each chunk in characters
        chunk_overlap: Overlap between consecutive chunks to preserve context

    Returns:
        List of KBRecord objects representing the chunks.
    """
    # Recursive splitter tries to break on paragraphs, then sentences, then words
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )

    chunks_text = splitter.split_text(content)
    kb_records = []

    import uuid
    for i, text in enumerate(chunks_text):
        # Create a unique ID for the chunk for precise vector db tracking
        # Qdrant strictly requires UUID format (e.g. string of 32 hex chars with or without hyphens)
        # We generate a deterministic UUID based on the doc_id and chunk index
        import hashlib
        hash_str = hashlib.md5(f"{doc_id}_chunk_{i}".encode()).hexdigest()
        record_id = str(uuid.UUID(hash_str))

        # Taxonomy Classifier Logic
        text_lower = text.lower()
        category = "product_info"
        if any(w in text_lower for w in ["rule", "must", "required", "policy"]):
            category = "policy_rules"
        elif any(w in text_lower for w in ["price", "cost", "premium"]):
            category = "pricing"
        elif any(w in text_lower for w in ["eligible", "qualify", "age"]):
            category = "eligibility_criteria"
        elif any(w in text_lower for w in ["claim", "reimburse"]):
            category = "claims_process"

        # Build schema-compliant record
        record = KBRecord(
            record_id=record_id,
            title=title,
            content=text,
            category=category,
            source=f"scraped/{doc_id}",
            source_url=source_url,
            pii_detected=pii_flags,
            chunk_index=i,
            parent_doc_id=doc_id,
        )
        kb_records.append(record)

    log.debug("document_chunked", doc_id=doc_id, chunks=len(kb_records))
    return kb_records


def chunk_documents(documents: List[Dict[str, Any]]) -> List[KBRecord]:
    """
    Process multiple cleaned documents into chunks.

    Args:
        documents: List of dicts output from cleaner.clean_document()

    Returns:
        Flattened list of all chunks across all documents.
    """
    all_chunks = []
    for doc in documents:
        # Generate a stable doc_id based on URL or content hash
        # SDE-3: Use deterministic MD5 instead of Python's randomized hash()
        import hashlib
        fallback_hash = hashlib.md5(doc["url"].encode()).hexdigest()
        doc_id = doc.get("content_hash", f"doc_{fallback_hash}")

        chunks = chunk_document(
            doc_id=doc_id,
            title=doc.get("title", "Untitled Document"),
            content=doc["content"],
            source_url=doc["url"],
            pii_flags=doc.get("pii_detected", False),
        )
        all_chunks.extend(chunks)

    log.info("batch_chunk_complete", documents=len(documents), total_chunks=len(all_chunks))
    return all_chunks
