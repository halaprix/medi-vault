from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from structlog import get_logger

from app.api.v1.router import router as v1_router
from app.core.logging_middleware import StructuredLoggingMiddleware

logger = get_logger()

app = FastAPI(title="medi-vault", version="0.1.0")

app.add_middleware(StructuredLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://frontend"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "db": "ok"}
