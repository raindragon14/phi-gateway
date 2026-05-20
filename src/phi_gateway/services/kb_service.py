"""Chunking, embedding, and semantic search for knowledge bases.

Uses OpenRouter embeddings with cosine similarity and a keyword
fallback when embedding generation is unavailable.
"""

import json
import logging
import math
import re
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from phi_gateway.core.embedding import generate_embedding, generate_embeddings_batch
from phi_gateway.core.exceptions import NotFoundError
from phi_gateway.models.api_key import ApiKey
from phi_gateway.models.document import Document, KnowledgeBase
from phi_gateway.schemas.knowledge import (
    IngestDocumentItem,
    KnowledgeBaseResponse,
    SearchResultItem,
)

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        a: First vector (list of floats).
        b: Second vector (list of floats).

    Returns:
        Cosine similarity in [-1.0, 1.0]. Returns 0.0 if either
        vector is empty or zero-norm.
    """
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks by paragraph boundaries.

    Args:
        text: Full document text to split.
        chunk_size: Maximum characters per chunk.
        overlap: Character overlap between consecutive chunks.

    Returns:
        List of text chunks. Returns empty list if ``text`` is empty.
    """
    if not text:
        return []

    chunks = []
    paragraphs = re.split(r"\n\s*\n", text)
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) + 1 <= chunk_size:
            current = (current + "\n\n" + para) if current else para
        else:
            if current:
                chunks.append(current)
            if len(para) > chunk_size:
                for i in range(0, len(para), chunk_size - overlap):
                    chunks.append(para[i : i + chunk_size])
                current = ""
            else:
                current = para

    if current:
        chunks.append(current)
    return chunks


async def create_kb(
    name: str,
    description: str,
    api_key: ApiKey,
    db: AsyncSession,
) -> KnowledgeBaseResponse:
    """Create a new knowledge base.

    Args:
        name: Display name for the knowledge base.
        description: Free-text description.
        api_key: The authenticated API key that owns this KB.
        db: Async database session.

    Returns:
        The newly created ``KnowledgeBaseResponse``.
    """
    kb = KnowledgeBase(
        name=name,
        description=description,
        api_key_id=api_key.id,
    )
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    return KnowledgeBaseResponse.model_validate(kb)


async def delete_kb(kb_id: UUID, api_key: ApiKey, db: AsyncSession) -> None:
    """Delete a knowledge base and all its documents.

    Args:
        kb_id: UUID of the knowledge base to delete.
        api_key: The authenticated API key (must own the KB).
        db: Async database session.

    Raises:
        HTTPException: 404 if the KB does not exist or is not owned
            by the caller.
    """
    await _get_owned_kb(kb_id, api_key, db)
    await db.execute(delete(Document).where(Document.kb_id == kb_id))
    await db.execute(delete(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    await db.commit()


async def ingest_documents(
    kb_id: UUID,
    documents: list[IngestDocumentItem],
    api_key: ApiKey,
    db: AsyncSession,
) -> tuple[int, list[str]]:
    """Ingest documents into a knowledge base: chunk, embed, store.

    Generates embeddings in a single batch call. Falls back to
    storing documents without vectors if embedding generation fails.

    Args:
        kb_id: UUID of the target knowledge base.
        documents: List of documents to ingest.
        api_key: The authenticated API key (must own the KB).
        db: Async database session.

    Returns:
        Tuple of ``(total_chunks, warnings)``. ``warnings`` is a
        list of non-fatal issues (e.g. embeddings unavailable).

    Raises:
        NotFoundError: If the KB does not exist or is not owned
            by the caller.
    """
    kb = await _get_owned_kb(kb_id, api_key, db)

    chunk_map: list[tuple[str, str, int, dict]] = []
    all_chunks: list[str] = []

    for doc in documents:
        chunks = _chunk_text(doc.content) or [doc.content or ""]
        for idx, chunk_text in enumerate(chunks):
            chunk_map.append((doc.title, chunk_text, idx, doc.metadata))
            all_chunks.append(chunk_text)

    total_chunks = len(all_chunks)

    # Generate embeddings in batch
    embeddings: list[list[float]] = []
    warnings: list[str] = []
    try:
        embeddings = await generate_embeddings_batch(all_chunks)
    except RuntimeError as e:
        logger.warning("Embeddings unavailable, storing without vectors: %s", e)
        embeddings = [[] for _ in all_chunks]
        warnings.append("Embeddings unavailable : documents stored without vectors, search will use keyword fallback")

    # Store chunks
    for (title, chunk_text, chunk_idx, metadata), embedding in zip(chunk_map, embeddings):
        doc = Document(
            kb_id=kb.id,
            title=title,
            content=chunk_text,
            chunk_index=chunk_idx,
            embedding=json.dumps(embedding).encode() if embedding else None,
            doc_metadata=metadata,
        )
        db.add(doc)

    kb.document_count = (kb.document_count or 0) + total_chunks
    await db.commit()
    return total_chunks, warnings


async def search_kb(
    kb_id: UUID,
    query: str,
    top_k: int,
    api_key: ApiKey,
    db: AsyncSession,
) -> list[SearchResultItem]:
    """Semantic search: embed query, cosine similarity, return top_k.

    Falls back to keyword (ILIKE) search if embedding generation fails.

    Args:
        kb_id: UUID of the knowledge base to search.
        query: Natural language search query.
        top_k: Number of top results to return.
        api_key: The authenticated API key (must own the KB).
        db: Async database session.

    Returns:
        List of ``SearchResultItem`` ordered by relevance (descending).

    Raises:
        HTTPException: 404 if the KB does not exist or is not owned
            by the caller.
    """
    await _get_owned_kb(kb_id, api_key, db)

    # Generate query embedding
    try:
        query_embedding = await generate_embedding(query)
    except RuntimeError as e:
        logger.warning("Embedding unavailable, using keyword fallback: %s", e)
        return await _keyword_search(db, kb_id, query, top_k)

    # Fetch all documents for this KB (size-limited for MVP)
    result = await db.execute(select(Document).where(Document.kb_id == kb_id))
    docs = result.scalars().all()

    # Score by cosine similarity
    scored: list[tuple[Document, float]] = []
    for doc in docs:
        if doc.embedding:
            try:
                doc_vec = json.loads(doc.embedding.decode())
                score = _cosine_similarity(query_embedding, doc_vec)
                scored.append((doc, score))
            except (json.JSONDecodeError, UnicodeDecodeError):
                scored.append((doc, 0.0))
        else:
            scored.append((doc, 0.0))

    scored.sort(key=lambda x: -x[1])

    return [
        SearchResultItem(
            content=doc.content,
            score=round(score, 4),
            metadata=doc.doc_metadata,
        )
        for doc, score in scored[:top_k]
    ]


async def _keyword_search(
    db: AsyncSession,
    kb_id: UUID | str,
    query: str,
    top_k: int,
) -> list[SearchResultItem]:
    """Fallback keyword search using ILIKE substring matching.

    Args:
        db: Async database session.
        kb_id: UUID of the knowledge base to search.
        query: Search query string.
        top_k: Maximum number of results to return.

    Returns:
        List of ``SearchResultItem`` with score set to 1.0.
    """
    result = await db.execute(
        select(Document).where(Document.kb_id == kb_id, Document.content.ilike(f"%{query}%")).limit(top_k)
    )
    docs = result.scalars().all()
    return [SearchResultItem(content=doc.content, score=1.0, metadata=doc.doc_metadata) for doc in docs]


async def _get_owned_kb(kb_id: UUID, api_key: ApiKey, db: AsyncSession) -> KnowledgeBase:
    """Fetch a knowledge base by ID, ensuring the caller owns it.

    Args:
        kb_id: UUID of the knowledge base.
        api_key: The authenticated API key.
        db: Async database session.

    Returns:
        The ``KnowledgeBase`` instance.

    Raises:
        HTTPException: 404 if the KB does not exist or is not owned
            by the caller.
    """
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.api_key_id == api_key.id,
        )
    )
    kb = result.scalar_one_or_none()
    if kb is None:
        raise NotFoundError("Knowledge base", str(kb_id))
    return kb
