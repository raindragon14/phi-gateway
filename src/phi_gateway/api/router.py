"""API router assembly — aggregates all resource routers into a single v1 prefix.

Every sub-router is mounted under ``/v1`` so all endpoints share
a consistent versioned base path.
"""

from fastapi import APIRouter

from phi_gateway.api.chat import router as chat_router
from phi_gateway.api.dashboard import router as dashboard_router
from phi_gateway.api.embeddings import router as embeddings_router
from phi_gateway.api.keys import router as keys_router
from phi_gateway.api.knowledge import router as knowledge_router
from phi_gateway.api.mcp import router as mcp_router
from phi_gateway.api.memory import router as memory_router
from phi_gateway.api.models import router as models_router
from phi_gateway.api.tools import router as tools_router
from phi_gateway.api.usage import router as usage_router

api_router = APIRouter()
"""Top-level v1 API router that includes all resource sub-routers."""

api_router.include_router(chat_router)
api_router.include_router(dashboard_router)
api_router.include_router(embeddings_router)
api_router.include_router(keys_router)
api_router.include_router(knowledge_router)
api_router.include_router(mcp_router)
api_router.include_router(memory_router)
api_router.include_router(models_router)
api_router.include_router(tools_router)
api_router.include_router(usage_router)
