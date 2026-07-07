# api/routes/auth.py
"""
Auth endpoints: /api/auth/register, /api/auth/login, /api/auth/me

Protected routes read the current user via get_current_user() dependency.
"""

import threading
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.security import create_token, decode_token, hash_password, verify_password
from models import user as user_model
from schemas.auth import LoginRequest, RegisterRequest

router = APIRouter()

_bearer = HTTPBearer()

# === Rate limiting ===
# Sliding window per client IP on credential endpoints. In-memory: resets on
# restart and is per-process, which is enough to stop online brute force on
# a single-instance deployment.
_RATE_LIMIT_ATTEMPTS = 5
_RATE_LIMIT_WINDOW_SECONDS = 60

_attempts: dict[str, list[float]] = {}
_attempts_lock = threading.Lock()


def _check_rate_limit(request: Request) -> None:
    """Raise 429 if this client IP exceeded the attempt budget for the window."""
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with _attempts_lock:
        window = [
            t for t in _attempts.get(ip, []) if now - t < _RATE_LIMIT_WINDOW_SECONDS
        ]
        if len(window) >= _RATE_LIMIT_ATTEMPTS:
            _attempts[ip] = window
            raise HTTPException(
                status_code=429, detail="too_many_attempts_try_again_later"
            )
        window.append(now)
        _attempts[ip] = window


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    """
    FastAPI dependency - extracts and validates the Bearer token.
    Inject into any route that requires an authenticated user:

        @router.get("/protected")
        async def protected(user: dict = Depends(get_current_user)):
            ...user["id"], user["email"]...
    """
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="invalid_or_expired_token")

    user = user_model.get_by_id(payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="user_not_found")

    return user


@router.post("/register")
async def register(body: RegisterRequest, request: Request) -> JSONResponse:
    _check_rate_limit(request)
    if user_model.email_exists(body.email):
        raise HTTPException(status_code=409, detail="email_already_registered")

    hashed = hash_password(body.password)
    user = user_model.create(body.email, hashed)
    token = create_token(user["id"], user["email"])

    return JSONResponse(
        {"token": token, "user_id": user["id"], "email": user["email"]}, status_code=201
    )


@router.post("/login")
async def login(body: LoginRequest, request: Request) -> JSONResponse:
    _check_rate_limit(request)
    user = user_model.get_by_email(body.email)
    if not user or not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="invalid_credentials")

    token = create_token(user["id"], user["email"])
    return JSONResponse({"token": token, "user_id": user["id"], "email": user["email"]})


@router.get("/me")
async def me(user: dict = Depends(get_current_user)) -> JSONResponse:
    return JSONResponse(
        {
            "user_id": user["id"],
            "email": user["email"],
            "created_at": user["created_at"],
        }
    )
