"""
q2_knowledge_base/chunker.py — Semantic chunking for RAG

Breaks cleaned text into manageable overlapping chunks.
Maintains traceability to the source document and preserves metadata.
"""

from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter

from shared.logger import get_logger
from q2_knowledge_base.schema import KBRecord, ChunkMetadata

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

    for i, text in enumerate(chunks_text):
        # Create a unique ID for the chunk for precise vector db tracking
        chunk_id = f"{doc_id}_chunk_{i}"

        # Build schema-compliant metadata
        metadata = ChunkMetadata(
            source_url=source_url,
            doc_id=doc_id,
            chunk_index=i,
            total_chunks=len(chunks_text),
            has_pii=pii_flags,
        )

        record = KBRecord(
            id=chunk_id,
            title=title,
            content=text,
            metadata=metadata,
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
        # We'll use content_hash from cleaner if available, else fallback
        doc_id = doc.get("content_hash", f"doc_{hash(doc['url'])}")

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
