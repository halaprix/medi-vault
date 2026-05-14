"""Biomarkers API — reference data."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func

from app.core.database import AsyncSession, get_db
from app.core.deps import get_current_user
from app.models import Biomarker, BiomarkerCategory, TestResult, User

router = APIRouter(prefix="/biomarkers", tags=["biomarkers"])


@router.get("/")
async def list_biomarkers(
    q: str = Query(None, description="Search by name"),
    category: str = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(Biomarker)
    if q:
        query = query.where(Biomarker.display_name.ilike(f"%{q}%"))
    if category:
        query = query.where(Biomarker.category == category)
    query = query.order_by(Biomarker.category, Biomarker.display_name).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return [
        {
            "id": str(b.id),
            "loinc_code": b.loinc_code,
            "display_name": b.display_name,
            "category": b.category.value,
            "standard_unit": b.standard_unit,
            "description": b.description,
            "aliases": b.aliases,
        }
        for b in result.scalars().all()
    ]


@router.get("/{biomarker_id}")
async def get_biomarker(biomarker_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Biomarker).where(Biomarker.id == biomarker_id))
    b = result.scalar_one_or_none()
    if not b:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Biomarker not found")
    return {
        "id": str(b.id),
        "loinc_code": b.loinc_code,
        "display_name": b.display_name,
        "standard_name": b.standard_name,
        "category": b.category.value,
        "standard_unit": b.standard_unit,
        "description": b.description,
        "aliases": b.aliases,
    }


@router.get("/categories/list")
async def list_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            Biomarker.category,
            func.count(TestResult.id.distinct()).label("result_count"),
        )
        .outerjoin(TestResult, (Biomarker.id == TestResult.biomarker_id) & (TestResult.user_id == current_user.id))
        .group_by(Biomarker.category)
        .order_by(Biomarker.category)
    )
    return [
        {"category": row.category.value, "result_count": row.result_count}
        for row in result.all()
    ]
