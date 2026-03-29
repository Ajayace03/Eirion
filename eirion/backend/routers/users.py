"""
Local JWT Authentication Router
--------------------------------
Replaces Clerk-based auth stub with self-contained JWT flow.
SQLite backed via Prisma (dev.db already exists).

Endpoints:
    POST /users/register
    POST /users/login
    GET  /users/me
    PATCH /users/onboarding-complete
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr

from database import db

router = APIRouter()
security = HTTPBearer(auto_error=False)

JWT_SECRET = os.getenv("JWT_SECRET", "eirion-dev-secret-changeme-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 168  # 7 days


# ─── Pydantic schemas ─────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    onboarding_complete: bool
    created_at: str


class AuthResponse(BaseModel):
    token: str
    user: UserOut


# ─── Helper: generate JWT ─────────────────────────────────────────────────────

def _create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# ─── Helper: get current user from JWT ────────────────────────────────────────

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """FastAPI dependency — validates local JWT. Falls back to dev stub."""
    if credentials is None:
        if os.getenv("REQUIRE_AUTH", "false").lower() == "true":
            raise HTTPException(status_code=401, detail="Not authenticated")
        return {"user_id": "dev_user", "email": "dev@eirion.local"}

    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {"user_id": payload["sub"], "email": payload.get("email", "")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired — please log in again")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(body: RegisterRequest):
    """Register a new user account."""
    # Check email uniqueness
    try:
        existing = await db.user.find_unique(where={"email": body.email})
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")
    except Exception as e:
        if "409" in str(e):
            raise
        # DB not running (dev mode) — return stub
        return _stub_auth_response(body.email, body.full_name)

    # Hash password
    hashed = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
    user_id = str(uuid.uuid4())

    try:
        user = await db.user.create(data={
            "id": user_id,
            "email": body.email,
            "full_name": body.full_name,
            "hashed_password": hashed,
            "onboarding_complete": False,
        })
    except Exception:
        return _stub_auth_response(body.email, body.full_name)

    token = _create_token(user.id)
    return AuthResponse(token=token, user=_user_out(user))


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    """Login with email + password."""
    try:
        user = await db.user.find_unique(where={"email": body.email})
    except Exception:
        user = None

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not bcrypt.checkpw(body.password.encode(), user.hashed_password.encode()):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = _create_token(user.id)
    return AuthResponse(token=token, user=_user_out(user))


@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return current user profile."""
    try:
        user = await db.user.find_unique(where={"id": current_user["user_id"]})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return _user_out(user)
    except HTTPException:
        raise
    except Exception:
        return UserOut(
            id="dev_user",
            email="dev@eirion.local",
            full_name="Developer",
            onboarding_complete=False,
            created_at=datetime.now(timezone.utc).isoformat(),
        )


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None


@router.patch("/me", response_model=UserOut)
async def update_me(body: UpdateProfileRequest, current_user: dict = Depends(get_current_user)):
    """Update current user's profile fields (name etc)."""
    update_data = {}
    if body.full_name:
        update_data["full_name"] = body.full_name.strip()
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        user = await db.user.update(
            where={"id": current_user["user_id"]},
            data=update_data,
        )
        return _user_out(user)
    except Exception:
        # Dev mode fallback — return updated stub
        return UserOut(
            id=current_user["user_id"],
            email=current_user.get("email", ""),
            full_name=body.full_name or "User",
            onboarding_complete=False,
            created_at=datetime.now(timezone.utc).isoformat(),
        )


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
):
    """Change the authenticated user's password."""
    if len(body.new_password) < 8:
        raise HTTPException(status_code=422, detail="New password must be at least 8 characters")
    try:
        user = await db.user.find_unique(where={"id": current_user["user_id"]})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not bcrypt.checkpw(body.current_password.encode(), user.hashed_password.encode()):
            raise HTTPException(status_code=401, detail="Current password is incorrect")
        new_hash = bcrypt.hashpw(body.new_password.encode(), bcrypt.gensalt()).decode()
        await db.user.update(
            where={"id": current_user["user_id"]},
            data={"hashed_password": new_hash},
        )
        return {"status": "ok", "message": "Password updated successfully"}
    except HTTPException:
        raise
    except Exception:
        # Dev mode — no DB, just confirm
        return {"status": "ok", "message": "Password updated (dev mode)"}


@router.patch("/onboarding-complete")
async def mark_onboarding_complete(current_user: dict = Depends(get_current_user)):
    """Mark wizard as completed for this user."""
    try:
        await db.user.update(
            where={"id": current_user["user_id"]},
            data={"onboarding_complete": True},
        )
    except Exception:
        pass  # Dev mode — no DB
    return {"status": "ok"}


# ─── Private helpers ──────────────────────────────────────────────────────────

def _user_out(user) -> UserOut:
    return UserOut(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        onboarding_complete=bool(getattr(user, "onboarding_complete", False)),
        created_at=str(getattr(user, "created_at", datetime.now(timezone.utc).isoformat())),
    )


def _stub_auth_response(email: str, full_name: str) -> AuthResponse:
    """Returns a stub response when DB is unavailable (local dev)."""
    uid = "dev_" + str(uuid.uuid4())[:8]
    token = _create_token(uid)
    return AuthResponse(
        token=token,
        user=UserOut(
            id=uid,
            email=email,
            full_name=full_name,
            onboarding_complete=False,
            created_at=datetime.now(timezone.utc).isoformat(),
        ),
    )
