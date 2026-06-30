import json
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func, desc

from ..db.database import get_db
from ..db.models import Check
from ..schemas import CheckResponse, StatsResponse

router = APIRouter()

def _row_to_response(r: Check) -> CheckResponse:
    return CheckResponse(
        id=r.id,
        input_text=r.input_text,
        score=r.score,
        verdict=r.verdict,
        reasons=json.loads(r.reasons),
        official_source=r.official_source or "",
        summary=r.summary or "",
        entities=json.loads(r.entities) if r.entities else [],
        ml_confidence=r.ml_confidence,
        created_at=r.created_at.isoformat(),
        cache_hit=False,
    )

@router.get("/checks", response_model=list[CheckResponse])
async def get_checks(
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Check).order_by(desc(Check.created_at)).limit(limit)
    )
    rows = result.scalars().all()
    return [_row_to_response(r) for r in rows]

@router.get("/checks/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("""
            SELECT
              COUNT(*)::int                                                AS total,
              COUNT(*) FILTER (WHERE verdict = 'Likely Fake')::int        AS likely_fake,
              COUNT(*) FILTER (WHERE verdict = 'Unverified')::int         AS unverified,
              COUNT(*) FILTER (WHERE verdict = 'Verified')::int           AS verified,
              ROUND(AVG(score)::numeric, 1)                               AS avg_score,
              MAX(created_at)                                              AS most_recent_date
            FROM verifyit_ds_checks
        """)
    )
    row = result.fetchone()
    if not row or row.total == 0:
        return StatsResponse(total=0, likely_fake=0, unverified=0, verified=0, avg_score=0, most_recent_date=None)

    return StatsResponse(
        total=row.total,
        likely_fake=row.likely_fake,
        unverified=row.unverified,
        verified=row.verified,
        avg_score=float(row.avg_score or 0),
        most_recent_date=row.most_recent_date.isoformat() if row.most_recent_date else None,
    )
