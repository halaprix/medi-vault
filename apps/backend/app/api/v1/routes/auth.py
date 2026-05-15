"""Authentication routes — PIN-based local auth + Google OAuth."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc

from app.core.database import AsyncSession, get_db
from app.core.deps import get_current_user
from app.core.rate_limiter import RateLimitExceeded, rate_limiter
from app.core.security import create_access_token, decrypt, encrypt, hash_pin, verify_pin
from app.models import SyncJob, User

router = APIRouter(prefix="/auth", tags=["auth"])


class PinSetupRequest(BaseModel):
    pin: str = Field(..., min_length=4, max_length=8, pattern=r"^\d+$")


class PinLoginRequest(BaseModel):
    pin: str = Field(..., min_length=4, max_length=8, pattern=r"^\d+$")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class StatusResponse(BaseModel):
    is_setup: bool
    is_authenticated: bool = False


class GoogleConnectResponse(BaseModel):
    auth_url: str


class GoogleStatusResponse(BaseModel):
    connected: bool
    token_expiry: str | None = None
    last_sync: str | None = None


# ── Routes ───────────────────────────────────────────

@router.get("/status", response_model=StatusResponse)
async def auth_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(func.count()).select_from(User))
    count = result.scalar()
    return StatusResponse(is_setup=count > 0)


@router.post("/setup", response_model=TokenResponse)
async def auth_setup(body: PinSetupRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(func.count()).select_from(User))
    count = result.scalar()
    if count > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already set up")
    user = User(settings_json={"pin_hash": hash_pin(body.pin)})
    db.add(user)
    await db.commit()
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def auth_login(body: PinLoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    # Rate limiting: 5 attempts/min per IP
    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:login:{client_ip}"
    try:
        await rate_limiter.check(key, max_requests=5, window_seconds=60)
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=429,
            detail=f"Too many login attempts. Retry after {e.retry_after}s.",
            headers={"Retry-After": str(e.retry_after)},
        )

    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not set up yet")
    pin_hash = user.settings_json.get("pin_hash", "")
    if not verify_pin(body.pin, pin_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect PIN")
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.post("/logout")
async def auth_logout(current_user: User = Depends(get_current_user)):
    return {"message": "Logged out"}


# ── Google OAuth ─────────────────────────────────────

@router.get("/google/connect", response_model=GoogleConnectResponse)
async def google_connect(
    current_user: User = Depends(get_current_user),
):
    """Generate Google OAuth2 authorization URL for Google Fit connection."""
    from app.core.config import settings
    from app.services.google_fit_service import GoogleFitService

    gf = GoogleFitService()
    redirect_uri = settings.google_redirect_uri
    auth_url, state = gf.get_auth_url(redirect_uri)
    return GoogleConnectResponse(auth_url=auth_url)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth2 callback — exchange code for tokens."""
    from app.core.config import settings

    # Find the user (single-user system)
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="No user set up")

    from app.services.google_fit_service import GoogleFitService
    gf = GoogleFitService()
    redirect_uri = settings.google_redirect_uri
    tokens = await gf.exchange_code(code, redirect_uri)

    # Encrypt and store tokens
    user.google_oauth_token = encrypt(tokens["access_token"])
    if tokens.get("refresh_token"):
        user.google_refresh_token = encrypt(tokens["refresh_token"])
    if tokens.get("expiry"):
        user.google_token_expiry = tokens["expiry"]
    await db.commit()

    return {"connected": True, "message": "Google Fit connected successfully"}


@router.delete("/google/disconnect")
async def google_disconnect(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke Google tokens and disconnect Google Fit."""
    # Nullify stored tokens (preserve synced data)
    current_user.google_oauth_token = None
    current_user.google_refresh_token = None
    current_user.google_token_expiry = None
    await db.commit()
    return {"connected": False, "message": "Google Fit disconnected"}


@router.get("/google/status")
async def google_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return Google Fit connection status."""
    connected = bool(current_user.google_oauth_token)
    expiry = None
    last_sync = None

    if connected and current_user.google_token_expiry:
        expiry = current_user.google_token_expiry.isoformat()

    # Get last sync job
    if connected:
        job_result = await db.execute(
            select(SyncJob)
            .where(SyncJob.user_id == current_user.id, SyncJob.job_type == "google_fit_sync")
            .order_by(desc(SyncJob.completed_at))
            .limit(1)
        )
        job = job_result.scalar_one_or_none()
        if job and job.completed_at:
            last_sync = job.completed_at.isoformat()

    return GoogleStatusResponse(
        connected=connected,
        token_expiry=expiry,
        last_sync=last_sync,
    )


# ── Sync Jobs ─────────────────────────────────────────

@router.get("/sync/jobs")
async def list_sync_jobs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List recent sync job history."""
    q = (
        select(SyncJob)
        .where(SyncJob.user_id == current_user.id)
        .order_by(desc(SyncJob.started_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(q)
    jobs = result.scalars().all()
    return [
        {
            "id": str(j.id),
            "job_type": j.job_type.value,
            "status": j.status.value,
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "completed_at": j.completed_at.isoformat() if j.completed_at else None,
            "error_message": j.error_message,
            "records_synced": j.records_synced,
        }
        for j in jobs
    ]
