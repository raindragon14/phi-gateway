"""Usage analytics — aggregate queries grouped by provider and model."""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from phi_gateway.schemas.usage import ModelBreakdown, ProviderBreakdown, UsageResponse

logger = logging.getLogger(__name__)


async def get_usage_stats(
    db: AsyncSession,
    api_key_id: str,
    from_date: str | None = None,
    to_date: str | None = None,
) -> UsageResponse:
    """Query usage statistics for an API key, grouped by provider and model.

    Uses parameterized SQL to avoid injection via the date string
    parameters.

    Args:
        db: Async database session.
        api_key_id: UUID string of the API key to query.
        from_date: Optional ISO date lower bound (inclusive), e.g.
            ``"2026-01-01"``.
        to_date: Optional ISO date upper bound (inclusive), e.g.
            ``"2026-12-31"``.

    Returns:
        A ``UsageResponse`` with totals and per-provider/model
        breakdowns.
    """
    base_conditions = "api_key_id = :api_key_id"
    # SQLite stores UUIDs without dashes — normalize the key ID
    db_key_id = api_key_id.replace("-", "")
    params: dict = {"api_key_id": db_key_id}

    if from_date:
        base_conditions += " AND created_at >= :from_date"
        params["from_date"] = from_date
    if to_date:
        base_conditions += " AND created_at <= :to_date"
        params["to_date"] = to_date

    # --- Total aggregation ---
    total_result = await db.execute(
        text(f"""
            SELECT
                COUNT(*) as total_requests,
                COALESCE(SUM(input_tokens), 0) as total_input_tokens,
                COALESCE(SUM(output_tokens), 0) as total_output_tokens,
                COALESCE(SUM(cost_usd_micro), 0) as total_cost_micro
            FROM llm_requests
            WHERE {base_conditions}
        """),
        params,
    )
    total_row = total_result.one()

    # --- By provider ---
    provider_result = await db.execute(
        text(f"""
            SELECT
                provider,
                COUNT(*) as requests,
                COALESCE(SUM(cost_usd_micro), 0) as cost_micro
            FROM llm_requests
            WHERE {base_conditions}
            GROUP BY provider
            ORDER BY cost_micro DESC
        """),
        params,
    )
    by_provider = [
        ProviderBreakdown(
            provider=r[0],
            requests=r[1],
            cost_usd=round(r[2] / 1_000_000, 6),
        )
        for r in provider_result.fetchall()
    ]

    # --- By model ---
    model_result = await db.execute(
        text(f"""
            SELECT
                model,
                COUNT(*) as requests,
                COALESCE(SUM(cost_usd_micro), 0) as cost_micro
            FROM llm_requests
            WHERE {base_conditions}
            GROUP BY model
            ORDER BY cost_micro DESC
        """),
        params,
    )
    by_model = [
        ModelBreakdown(
            model=r[0],
            requests=r[1],
            cost_usd=round(r[2] / 1_000_000, 6),
        )
        for r in model_result.fetchall()
    ]

    return UsageResponse(
        total_requests=total_row[0],
        total_input_tokens=total_row[1],
        total_output_tokens=total_row[2],
        total_cost_usd=round(total_row[3] / 1_000_000, 6),
        by_provider=by_provider,
        by_model=by_model,
    )
