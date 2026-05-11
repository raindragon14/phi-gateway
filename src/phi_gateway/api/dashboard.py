from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Dashboard"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "dashboard" / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_overview(request: Request):
    """Dashboard: Overview page."""
    return templates.TemplateResponse("overview.html", {"request": request, "active": "overview"})


@router.get("/dashboard/keys", response_class=HTMLResponse)
async def dashboard_keys(request: Request):
    """Dashboard: API key management page."""
    return templates.TemplateResponse("keys.html", {"request": request, "active": "keys"})


@router.get("/dashboard/keys/table", response_class=HTMLResponse)
async def dashboard_keys_table(request: Request):
    """HTMX endpoint: keys table fragment."""
    return templates.TemplateResponse("keys_table.html", {"request": request})


@router.get("/dashboard/usage", response_class=HTMLResponse)
async def dashboard_usage(request: Request):
    """Dashboard: Usage page."""
    return templates.TemplateResponse("usage.html", {"request": request, "active": "usage"})


@router.get("/dashboard/docs", response_class=HTMLResponse)
async def dashboard_docs(request: Request):
    """Dashboard: Documentation page."""
    return templates.TemplateResponse("docs.html", {"request": request, "active": "docs"})


@router.get("/dashboard/memory", response_class=HTMLResponse)
async def dashboard_memory(request: Request):
    """Dashboard: Agent memory page."""
    return templates.TemplateResponse("memory.html", {"request": request, "active": "memory"})
