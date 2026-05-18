from fastapi import APIRouter, Query

from phi_gateway.core.llm_proxy import list_models

router = APIRouter(prefix="/v1", tags=["Models"])


@router.get("/models")
async def get_models(
    provider: str | None = Query(None, description="Filter by provider (e.g. openai, anthropic, groq, openrouter)"),
    search: str | None = Query(None, description="Search model IDs (case-insensitive substring match)"),
):
    """List all available models across all configured providers.

    Optional query params:
    - ``provider``: filter by provider name
    - ``search``: substring match on model ID
    """
    models = list_models()

    if provider:
        models = [m for m in models if m["provider"] == provider]

    if search:
        q = search.lower()
        models = [m for m in models if q in m["id"].lower()]

    return models
