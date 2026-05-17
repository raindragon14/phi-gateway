import logging

import openai

from phi_gateway.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


async def generate_embedding(text: str, model: str = "text-embedding-3-small") -> list[float]:
    """Generate an embedding vector using OpenRouter.

    Uses OPENROUTER_API_KEY from .env (no separate OpenAI key needed).
    Returns a list of floats (the embedding vector).
    Raises RuntimeError if OpenRouter is not configured.
    """
    if not settings.OPENROUTER_API_KEY:
        raise RuntimeError(
            "OpenRouter API key is not configured. "
            "Set OPENROUTER_API_KEY in .env to use embeddings."
        )

    client = openai.AsyncOpenAI(
        api_key=settings.OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    )
    try:
        response = await client.embeddings.create(
            model=model,
            input=text,
        )
        return response.data[0].embedding
    except Exception as e:
        logger.exception("Embedding generation failed")
        raise RuntimeError(f"Embedding generation failed: {e}")


async def generate_embeddings_batch(
    texts: list[str],
    model: str = "text-embedding-3-small",
) -> list[list[float]]:
    """Generate embeddings for a batch of texts via OpenRouter."""
    if not settings.OPENROUTER_API_KEY:
        raise RuntimeError(
            "OpenRouter API key is not configured. "
            "Set OPENROUTER_API_KEY in .env to use embeddings."
        )

    client = openai.AsyncOpenAI(
        api_key=settings.OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    )
    try:
        response = await client.embeddings.create(
            model=model,
            input=texts,
        )
        # Sort by index to maintain order
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [d.embedding for d in sorted_data]
    except Exception as e:
        logger.exception("Batch embedding generation failed")
        raise RuntimeError(f"Batch embedding generation failed: {e}")
