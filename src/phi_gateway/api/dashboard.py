"""HTMX dashboard routes — serve the admin UI."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Dashboard"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "dashboard" / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/dashboard")
async def dashboard_overview():
    """Dashboard: Overview page."""
    return templates.TemplateResponse("overview.html", {"active": "overview"})


@router.get("/dashboard/keys")
async def dashboard_keys():
    """Dashboard: API key management page."""
    return templates.TemplateResponse("keys.html", {"active": "keys"})


@router.get("/dashboard/keys/table")
async def dashboard_keys_table():
    """HTMX endpoint: keys table fragment."""
    return templates.TemplateResponse("keys_table.html", {})


@router.get("/dashboard/usage")
async def dashboard_usage():
    """Dashboard: Usage page."""
    return templates.TemplateResponse("usage.html", {"active": "usage"})


@router.get("/dashboard/docs")
async def dashboard_docs():
    """Dashboard: Documentation page."""
    return templates.TemplateResponse("docs.html", {"active": "docs"})


@router.get("/dashboard/memory")
async def dashboard_memory():
    """Dashboard: Agent memory page."""
    return templates.TemplateResponse("memory.html", {"active": "memory"})
