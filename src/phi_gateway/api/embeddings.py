"""OpenAI-compatible embeddings endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from phi_gateway.core.embedding import generate_embedding, generate_embeddings_batch
from phi_gateway.dependencies import get_api_key
from phi_gateway.models.api_key import ApiKey


class EmbeddingRequest(BaseModel):
    """Request schema for embedding generation.

    Attributes:
        model: Embedding model identifier.
        input: Single text string or list of texts to embed.
    """

    model: str
    input: str | list[str]


router = APIRouter(prefix="/v1", tags=["Embeddings"])


@router.post("/embeddings")
async def create_embeddings(
    body: EmbeddingRequest,
    api_key: ApiKey = Depends(get_api_key),
):
    """Generate embeddings for the given input text(s).

    Args:
        body: Request with model identifier and input text(s).
        api_key: Authenticated API key (from dependency injection).

    Returns:
        OpenAI-compatible embedding response with ``object``,
        ``data``, ``model``, and ``usage`` keys.

    Raises:
        HTTPException: 502 if embedding generation fails (e.g.
            OpenRouter not configured).
    """
    try:
        if isinstance(body.input, str):
            vectors = [await generate_embedding(body.input, body.model)]
        else:
            vectors = await generate_embeddings_batch(body.input, body.model)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )

    return {
        "object": "list",
        "data": [
            {
                "object": "embedding",
                "index": i,
                "embedding": vec,
            }
            for i, vec in enumerate(vectors)
        ],
        "model": body.model,
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }
