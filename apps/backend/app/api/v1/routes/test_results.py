"""Test Results API — CRUD, trends, summary, out-of-range."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, desc, func

from app.core.database import AsyncSession, get_db
from app.core.deps import get_current_user
from app.models import Biomarker, OutOfRangeDirection, TestResult, User

router = APIRouter(prefix="/results", tags=["results"])


class ResultOut(BaseModel):
    id: str
    biomarker_display_name: str
    biomarker_id: str
    value: float
    standard_unit: str
    result_date: str
    is_out_of_range: bool
    out_of_range_direction: str
    document_id: str
    ref_range_low: Optional[float] = None
    ref_range_high: Optional[float] = None


class TrendPoint(BaseModel):
    date: str
    value: float
    unit: str
    is_out_of_range: bool
    ref_range_low: Optional[float] = None
    ref_range_high: Optional[float] = None


class TrendResponse(BaseModel):
    biomarker: dict
    trend: list[TrendPoint]


class SummaryCategory(BaseModel):
    name: str
    has_out_of_range: bool
    most_recent_date: Optional[str] = None
    marker_count: int


class NotesUpdate(BaseModel):
    notes: str


# ── Routes ───────────────────────────────────────────

@router.get("/")
async def list_results(
    biomarker_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_out_of_range: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(TestResult, Biomarker)
        .join(Biomarker, TestResult.biomarker_id == Biomarker.id)
        .where(TestResult.user_id == current_user.id)
    )
    if biomarker_id:
        q = q.where(TestResult.biomarker_id == biomarker_id)
    if category:
        q = q.where(Biomarker.category == category)
    if is_out_of_range is not None:
        q = q.where(TestResult.is_out_of_range == is_out_of_range)
    q = q.order_by(desc(TestResult.result_date)).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    rows = result.all()
    return [
        ResultOut(
            id=str(r.TestResult.id),
            biomarker_display_name=r.Biomarker.display_name,
            biomarker_id=str(r.TestResult.biomarker_id),
            value=r.TestResult.value,
            standard_unit=r.TestResult.standard_unit or "",
            result_date=r.TestResult.result_date.isoformat(),
            is_out_of_range=r.TestResult.is_out_of_range,
            out_of_range_direction=r.TestResult.out_of_range_direction.value,
            document_id=str(r.TestResult.document_id),
            ref_range_low=r.TestResult.ref_range_low,
            ref_range_high=r.TestResult.ref_range_high,
        )
        for r in rows
    ]


@router.get("/trend/{biomarker_id}")
async def get_trend(
    biomarker_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bio = await db.execute(select(Biomarker).where(Biomarker.id == biomarker_id))
    biomarker = bio.scalar_one_or_none()
    if not biomarker:
        raise HTTPException(status_code=404, detail="Biomarker not found")

    result = await db.execute(
        select(TestResult)
        .where(TestResult.user_id == current_user.id, TestResult.biomarker_id == biomarker_id)
        .order_by(TestResult.result_date.asc())
    )
    results = result.scalars().all()
    return TrendResponse(
        biomarker={
            "id": str(biomarker.id),
            "display_name": biomarker.display_name,
            "standard_unit": biomarker.standard_unit,
        },
        trend=[
            TrendPoint(
                date=r.result_date.isoformat(),
                value=r.value,
                unit=r.standard_unit or "",
                is_out_of_range=r.is_out_of_range,
                ref_range_low=r.ref_range_low,
                ref_range_high=r.ref_range_high,
            )
            for r in results
        ],
    )


@router.get("/summary")
async def get_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import distinct
    sub = (
        select(
            TestResult.biomarker_id,
            func.max(TestResult.result_date).label("max_date"),
        )
        .where(TestResult.user_id == current_user.id)
        .group_by(TestResult.biomarker_id)
        .subquery()
    )
    result = await db.execute(
        select(TestResult, Biomarker)
        .join(sub, (TestResult.biomarker_id == sub.c.biomarker_id) & (TestResult.result_date == sub.c.max_date))
        .join(Biomarker)
        .where(TestResult.user_id == current_user.id)
        .order_by(Biomarker.category, Biomarker.display_name)
    )
    rows = result.all()
    return [
        {
            "biomarker_id": str(r.TestResult.biomarker_id),
            "display_name": r.Biomarker.display_name,
            "category": r.Biomarker.category.value,
            "latest_value": r.TestResult.value,
            "unit": r.TestResult.standard_unit,
            "date": r.TestResult.result_date.isoformat(),
            "is_out_of_range": r.TestResult.is_out_of_range,
        }
        for r in rows
    ]


@router.get("/out-of-range")
async def get_out_of_range(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = (
        select(
            TestResult.biomarker_id,
            func.max(TestResult.result_date).label("max_date"),
        )
        .where(TestResult.user_id == current_user.id, TestResult.is_out_of_range == True)
        .group_by(TestResult.biomarker_id)
        .subquery()
    )
    result = await db.execute(
        select(TestResult, Biomarker)
        .join(sub, (TestResult.biomarker_id == sub.c.biomarker_id) & (TestResult.result_date == sub.c.max_date))
        .join(Biomarker)
        .where(TestResult.user_id == current_user.id)
        .order_by(desc(TestResult.result_date))
    )
    rows = result.all()
    return [
        {
            "biomarker_id": str(r.TestResult.biomarker_id),
            "display_name": r.Biomarker.display_name,
            "value": r.TestResult.value,
            "unit": r.TestResult.standard_unit,
            "direction": r.TestResult.out_of_range_direction.value,
            "date": r.TestResult.result_date.isoformat(),
            "ref_range_low": r.TestResult.ref_range_low,
            "ref_range_high": r.TestResult.ref_range_high,
        }
        for r in rows
    ]


@router.patch("/{result_id}")
async def update_notes(
    result_id: str,
    body: NotesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TestResult).where(TestResult.id == result_id, TestResult.user_id == current_user.id)
    )
    tr = result.scalar_one_or_none()
    if not tr:
        raise HTTPException(status_code=404, detail="Result not found")
    tr.notes = body.notes
    await db.commit()
    return {"id": str(tr.id), "notes": tr.notes}


@router.delete("/{result_id}", status_code=204)
async def delete_result(
    result_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TestResult).where(TestResult.id == result_id, TestResult.user_id == current_user.id)
    )
    tr = result.scalar_one_or_none()
    if not tr:
        raise HTTPException(status_code=404, detail="Result not found")
    await db.delete(tr)
    await db.commit()
    return None
