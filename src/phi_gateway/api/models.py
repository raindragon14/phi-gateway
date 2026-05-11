from fastapi import APIRouter

from phi_gateway.core.llm_proxy import list_models

router = APIRouter(prefix="/v1", tags=["Models"])


@router.get("/models")
async def get_models():
    """List all available models across all configured providers."""
    return list_models()
