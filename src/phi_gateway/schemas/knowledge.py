from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreateKnowledgeBaseRequest(BaseModel):
    name: str
    description: str = ""


class KnowledgeBaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    document_count: int
    created_at: datetime


class IngestDocumentItem(BaseModel):
    title: str
    content: str
    metadata: dict[str, Any] = {}


class IngestDocumentsRequest(BaseModel):
    documents: list[IngestDocumentItem]


class IngestDocumentsResponse(BaseModel):
    total_chunks: int
    kb_id: UUID


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchResultItem(BaseModel):
    content: str
    score: float
    metadata: dict[str, Any] = {}


class SearchResponse(BaseModel):
    results: list[SearchResultItem]
