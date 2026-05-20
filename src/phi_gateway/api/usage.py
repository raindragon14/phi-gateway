"""Usage analytics API : token counts, cost breakdowns by provider and model."""

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from phi_gateway.database import get_db
from phi_gateway.dependencies import get_api_key
from phi_gateway.models.api_key import ApiKey
from phi_gateway.schemas.usage import UsageResponse
from phi_gateway.services.usage_service import get_usage_stats

router = APIRouter(prefix="/v1", tags=["Usage"])


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    api_key: ApiKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
):
    """Get usage statistics for the current API key.

    Returns token counts, cost breakdowns by provider and model.

    Args:
        api_key: Authenticated API key (used to scope results).
        db: Async database session.
        from_date: Optional ISO date lower bound (inclusive).
        to_date: Optional ISO date upper bound (inclusive).

    Returns:
        ``UsageResponse`` with totals and per-provider/model
        breakdowns.
    """
    return await get_usage_stats(db, str(api_key.id), from_date, to_date)
