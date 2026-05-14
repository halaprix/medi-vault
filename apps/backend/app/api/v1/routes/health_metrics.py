"""Health Metrics API — manual entry + retrieval."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, desc, func
from sqlalchemy.dialects.postgresql import insert

from app.core.database import AsyncSession, get_db
from app.core.deps import get_current_user
from app.models import HealthMetric, MetricSource, MetricType, User

router = APIRouter(prefix="/metrics", tags=["metrics"])


class MetricCreate(BaseModel):
    date: str
    metric_type: str
    value: float


# ── Routes ───────────────────────────────────────────

@router.get("/")
async def list_metrics(
    metric_type: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timedelta
    since = datetime.utcnow().date() - timedelta(days=days)
    q = select(HealthMetric).where(
        HealthMetric.user_id == current_user.id,
        HealthMetric.date >= since,
    )
    if metric_type:
        q = q.where(HealthMetric.metric_type == metric_type)
    q = q.order_by(desc(HealthMetric.date))
    result = await db.execute(q)
    return [
        {
            "id": str(m.id),
            "date": m.date.isoformat(),
            "metric_type": m.metric_type.value,
            "value": m.value,
            "source": m.source.value,
        }
        for m in result.scalars().all()
    ]


@router.post("/")
async def create_metric(
    body: MetricCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = insert(HealthMetric).values(
        user_id=current_user.id,
        date=date.fromisoformat(body.date),
        metric_type=body.metric_type,
        value=body.value,
        source=MetricSource.manual,
    ).on_conflict_do_update(
        index_elements=["user_id", "date", "metric_type"],
        set_={"value": body.value},
    )
    await db.execute(stmt)
    await db.commit()
    return {"date": body.date, "metric_type": body.metric_type, "value": body.value}


@router.delete("/{metric_id}", status_code=204)
async def delete_metric(
    metric_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(HealthMetric).where(HealthMetric.id == metric_id, HealthMetric.user_id == current_user.id)
    )
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Metric not found")
    await db.delete(m)
    await db.commit()
    return None


@router.get("/summary")
async def get_summary(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timedelta
    since = datetime.utcnow().date() - timedelta(days=days)
    result = await db.execute(
        select(
            HealthMetric.metric_type,
            func.avg(HealthMetric.value).label("avg"),
            func.max(HealthMetric.value).label("max"),
            func.min(HealthMetric.value).label("min"),
            func.count().label("count"),
        )
        .where(HealthMetric.user_id == current_user.id, HealthMetric.date >= since)
        .group_by(HealthMetric.metric_type)
    )
    return [
        {
            "metric_type": row.metric_type.value,
            "average": round(float(row.avg), 2) if row.avg else None,
            "max": round(float(row.max), 2) if row.max else None,
            "min": round(float(row.min), 2) if row.min else None,
            "count": row.count,
        }
        for row in result.all()
    ]
