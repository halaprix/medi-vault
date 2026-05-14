"""API v1 router — aggregates all route modules."""
from fastapi import APIRouter

from app.api.v1.routes import auth, biomarkers, documents, health_metrics, recommendations, test_results

router = APIRouter()

router.include_router(auth.router)
router.include_router(documents.router)
router.include_router(test_results.router)
router.include_router(health_metrics.router)
router.include_router(biomarkers.router)
router.include_router(recommendations.router)
