"""HTMX dashboard routes — serve the admin UI.

Supports both Bearer token (API clients) and cookie-based
authentication (browser users after login).
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from phi_gateway.dependencies import get_api_key
from phi_gateway.models.api_key import ApiKey

router = APIRouter(tags=["Dashboard"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "dashboard" / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ── Dashboard auth — admin/pro only ───────────────────────────────

async def _require_admin(api_key: ApiKey = Depends(get_api_key)) -> ApiKey:
    if api_key.tier not in ("admin", "pro"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dashboard access requires admin or pro tier API key",
        )
    return api_key


# ── Routes ────────────────────────────────────────────────────────

@router.get("/login")
async def login_page(request: Request):
    """Render the login page for dashboard access."""
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/logout")
async def logout():
    """Clear the session cookie and redirect to login."""
    response = RedirectResponse(url="/login")
    response.delete_cookie("phi_api_key", path="/")
    return response


@router.get("/dashboard")
async def dashboard_overview(
    request: Request,
    api_key: ApiKey = Depends(_require_admin),
):
    """Dashboard: Overview page."""
    return templates.TemplateResponse(
        "overview.html",
        {"request": request, "active": "overview"},
    )


@router.get("/dashboard/keys")
async def dashboard_keys(
    request: Request,
    api_key: ApiKey = Depends(_require_admin),
):
    """Dashboard: API key management page."""
    return templates.TemplateResponse(
        "keys.html",
        {"request": request, "active": "keys"},
    )


@router.get("/dashboard/keys/table")
async def dashboard_keys_table(
    request: Request,
    api_key: ApiKey = Depends(_require_admin),
):
    """HTMX endpoint: keys table fragment."""
    return templates.TemplateResponse(
        "keys_table.html",
        {"request": request},
    )


@router.get("/dashboard/usage")
async def dashboard_usage(
    request: Request,
    api_key: ApiKey = Depends(_require_admin),
):
    """Dashboard: Usage page."""
    return templates.TemplateResponse(
        "usage.html",
        {"request": request, "active": "usage"},
    )


@router.get("/dashboard/docs")
async def dashboard_docs(
    request: Request,
    api_key: ApiKey = Depends(_require_admin),
):
    """Dashboard: Documentation page."""
    return templates.TemplateResponse(
        "docs.html",
        {"request": request, "active": "docs"},
    )


@router.get("/dashboard/memory")
async def dashboard_memory(
    request: Request,
    api_key: ApiKey = Depends(_require_admin),
):
    """Dashboard: Agent memory page."""
    return templates.TemplateResponse(
        "memory.html",
        {"request": request, "active": "memory"},
    )
