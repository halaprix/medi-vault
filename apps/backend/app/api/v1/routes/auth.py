"""Authentication routes — PIN-based local auth."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func

from app.core.database import AsyncSession, get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_pin, verify_pin
from app.models import User

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
async def auth_login(body: PinLoginRequest, db: AsyncSession = Depends(get_db)):
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
