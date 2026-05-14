"""Recommendations API — generate, list, detail, dismiss."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, desc

from app.core.database import AsyncSession, get_db
from app.core.deps import get_current_user
from app.models import Recommendation, TestResult, User

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


class GenerateRequest(BaseModel):
    test_result_id: str


# ── Routes ───────────────────────────────────────────

@router.post("/generate")
async def generate_recommendation(
    body: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TestResult).where(TestResult.id == body.test_result_id, TestResult.user_id == current_user.id)
    )
    tr = result.scalar_one_or_none()
    if not tr:
        raise HTTPException(status_code=404, detail="Test result not found")
    if not tr.is_out_of_range:
        raise HTTPException(status_code=400, detail="Result is within normal range")

    rec = Recommendation(
        user_id=current_user.id,
        biomarker_id=tr.biomarker_id,
        test_result_id=tr.id,
        recommendation_text="Recommendation pending generation via RAG engine.",
    )
    db.add(rec)
    await db.commit()
    return {"recommendation_id": str(rec.id), "status": "generating"}


@router.get("/")
async def list_recommendations(
    biomarker_id: str | None = None,
    is_dismissed: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Recommendation).where(Recommendation.user_id == current_user.id)
    if biomarker_id:
        q = q.where(Recommendation.biomarker_id == biomarker_id)
    if is_dismissed is not None:
        q = q.where(Recommendation.is_dismissed == is_dismissed)
    q = q.order_by(desc(Recommendation.created_at))
    result = await db.execute(q)
    return [
        {
            "id": str(r.id),
            "biomarker_id": str(r.biomarker_id),
            "test_result_id": str(r.test_result_id),
            "recommendation_text": r.recommendation_text,
            "rag_context_used": r.rag_context_used,
            "is_dismissed": r.is_dismissed,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in result.scalars().all()
    ]


@router.get("/{recommendation_id}")
async def get_recommendation(
    recommendation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Recommendation).where(
            Recommendation.id == recommendation_id, Recommendation.user_id == current_user.id
        )
    )
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return {
        "id": str(r.id),
        "biomarker_id": str(r.biomarker_id),
        "test_result_id": str(r.test_result_id),
        "recommendation_text": r.recommendation_text,
        "rag_context_used": r.rag_context_used,
        "is_dismissed": r.is_dismissed,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@router.patch("/{recommendation_id}/dismiss")
async def dismiss_recommendation(
    recommendation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Recommendation).where(
            Recommendation.id == recommendation_id, Recommendation.user_id == current_user.id
        )
    )
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    r.is_dismissed = True
    await db.commit()
    return {"id": str(r.id), "is_dismissed": True}
