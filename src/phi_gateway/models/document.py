"""Knowledge base and document models for RAG functionality."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String, Text, Uuid
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from phi_gateway.models.base import Base


class KnowledgeBase(Base):
    """A named collection of documents for retrieval-augmented generation.

    Belongs to an API key owner. Tracks the total document/chunk count
    for quick metadata display without counting rows.

    Attributes:
        id: UUID primary key.
        name: Display name for this knowledge base.
        description: Optional free-text description.
        api_key_id: Foreign key to the owning API key.
        document_count: Cached count of documents (chunks) in this KB.
        created_at: Timestamp of creation (server default).
    """

    __tablename__ = "knowledge_bases"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    api_key_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("api_keys.id"), nullable=False
    )
    document_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class Document(Base):
    """A single chunk of text content stored in a knowledge base.

    Each document belongs to a ``KnowledgeBase`` and may optionally
    have an embedding vector (as raw bytes) for vector similarity
    search. Metadata is stored as a JSON column.

    Attributes:
        id: UUID primary key.
        kb_id: Foreign key to the parent knowledge base.
        title: Document/chunk title.
        content: Full text content.
        chunk_index: Position of this chunk within the document.
        embedding: Optional embedding vector bytes (float32 array).
        doc_metadata: Arbitrary JSON metadata dictionary.
        created_at: Timestamp of creation (server default).
    """

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    kb_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("knowledge_bases.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embedding: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True
    )
    doc_metadata: Mapped[dict] = mapped_column("metadata_json", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
