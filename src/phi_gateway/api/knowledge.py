from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from phi_gateway.database import get_db
from phi_gateway.dependencies import get_api_key
from phi_gateway.models.api_key import ApiKey
from phi_gateway.schemas.knowledge import (
    CreateKnowledgeBaseRequest,
    IngestDocumentsRequest,
    IngestDocumentsResponse,
    KnowledgeBaseResponse,
    SearchRequest,
    SearchResponse,
)
from phi_gateway.services.kb_service import create_kb, delete_kb, ingest_documents, search_kb

router = APIRouter(prefix="/v1/kb", tags=["Knowledge Base"])


@router.post("", response_model=KnowledgeBaseResponse, status_code=201)
async def create_kb_endpoint(
    body: CreateKnowledgeBaseRequest,
    api_key: ApiKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Create a new knowledge base.

    Args:
        body: Request with name and description.
        api_key: Authenticated API key (becomes the KB owner).
        db: Async database session.

    Returns:
        The newly created ``KnowledgeBaseResponse``.
    """
    return await create_kb(body.name, body.description, api_key, db)


@router.delete("/{kb_id}")
async def delete_kb_endpoint(
    kb_id: UUID,
    api_key: ApiKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Delete a knowledge base and all its documents.

    Args:
        kb_id: UUID of the knowledge base to delete.
        api_key: Authenticated API key (must own the KB).
        db: Async database session.

    Returns:
        Dict with ``"status"`` and ``"id"`` keys.

    Raises:
        HTTPException: 404 if the KB does not exist or is not owned
            by the caller.
    """
    await delete_kb(kb_id, api_key, db)
    return {"status": "deleted", "id": str(kb_id)}


@router.post("/{kb_id}/documents", response_model=IngestDocumentsResponse, status_code=201)
async def ingest_documents_endpoint(
    kb_id: UUID,
    body: IngestDocumentsRequest,
    api_key: ApiKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Ingest documents into a knowledge base (chunk → embed → store).

    Args:
        kb_id: UUID of the target knowledge base.
        body: Request with list of documents to ingest.
        api_key: Authenticated API key (must own the KB).
        db: Async database session.

    Returns:
        ``IngestDocumentsResponse`` with total chunks created and KB ID.

    Raises:
        HTTPException: 404 if the KB does not exist or is not owned
            by the caller.
    """
    total = await ingest_documents(kb_id, body.documents, api_key, db)
    return IngestDocumentsResponse(total_chunks=total, kb_id=kb_id)


@router.post("/{kb_id}/search", response_model=SearchResponse)
async def search_kb_endpoint(
    kb_id: UUID,
    body: SearchRequest,
    api_key: ApiKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Semantic search across a knowledge base.

    Args:
        kb_id: UUID of the knowledge base to search.
        body: Request with query string and top_k.
        api_key: Authenticated API key (must own the KB).
        db: Async database session.

    Returns:
        ``SearchResponse`` with results ordered by relevance.

    Raises:
        HTTPException: 404 if the KB does not exist or is not owned
            by the caller.
    """
    results = await search_kb(kb_id, body.query, body.top_k, api_key, db)
    return SearchResponse(results=results)
