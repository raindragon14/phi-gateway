"""Pydantic schemas for knowledge base management and RAG search."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreateKnowledgeBaseRequest(BaseModel):
    """Request body to create a new knowledge base.

    Attributes:
        name: Display name for the knowledge base.
        description: Optional free-text description.
    """

    name: str
    description: str = ""


class KnowledgeBaseResponse(BaseModel):
    """Public representation of a knowledge base.

    Attributes:
        id: UUID of the knowledge base.
        name: Display name.
        description: Free-text description.
        document_count: Number of documents (chunks) in this KB.
        created_at: Timestamp of creation.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    document_count: int
    created_at: datetime


class IngestDocumentItem(BaseModel):
    """A single document to be ingested into a knowledge base.

    Attributes:
        title: Document title.
        content: Full text content.
        metadata: Arbitrary key-value metadata dictionary.
    """

    title: str
    content: str
    metadata: dict[str, Any] = {}


class IngestDocumentsRequest(BaseModel):
    """Request body for batch document ingestion.

    Attributes:
        documents: List of documents to ingest.
    """

    documents: list[IngestDocumentItem]


class IngestDocumentsResponse(BaseModel):
    """Response after successful document ingestion.

    Attributes:
        total_chunks: Number of chunks created.
        kb_id: UUID of the knowledge base the documents were added to.
        warnings: Optional list of non-fatal issues encountered
            during ingestion (e.g. embeddings unavailable).
    """

    total_chunks: int
    kb_id: UUID
    warnings: list[str] = []


class SearchRequest(BaseModel):
    """Request body for semantic search over a knowledge base.

    Attributes:
        query: Search query string.
        top_k: Number of top results to return (default 5).
    """

    query: str
    top_k: int = 5


class SearchResultItem(BaseModel):
    """A single search result with content and relevance score.

    Attributes:
        content: The matching document chunk text.
        score: Relevance score (higher is better).
        metadata: Document metadata from the source.
    """

    content: str
    score: float
    metadata: dict[str, Any] = {}


class SearchResponse(BaseModel):
    """Response body for a knowledge base search.

    Attributes:
        results: List of search results ordered by relevance.
    """

    results: list[SearchResultItem]
