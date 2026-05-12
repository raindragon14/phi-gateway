"""OpenAI-compatible embeddings endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from phi_gateway.core.embedding import generate_embedding, generate_embeddings_batch
from phi_gateway.dependencies import get_api_key
from phi_gateway.models.api_key import ApiKey


class EmbeddingRequest(BaseModel):
    """Request schema for embedding generation."""
    model: str
    input: str | list[str]


router = APIRouter(prefix="/v1", tags=["Embeddings"])


@router.post("/embeddings")
async def create_embeddings(
    body: EmbeddingRequest,
    api_key: ApiKey = Depends(get_api_key),
):
    """Generate embeddings for the given input text(s)."""
    try:
        if isinstance(body.input, str):
            vectors = [await generate_embedding(body.input, body.model)]
            inputs = [body.input]
        else:
            vectors = await generate_embeddings_batch(body.input, body.model)
            inputs = body.input
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
