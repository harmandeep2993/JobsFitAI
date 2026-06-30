# api/routes/auth.py
"""
Auth endpoints: /api/auth/register, /api/auth/login, /api/auth/me

Protected routes read the current user via get_current_user() dependency.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.security import create_token, decode_token, hash_password, verify_password
from models import user as user_model
from schemas.auth import LoginRequest, RegisterRequest

router = APIRouter()

_bearer = HTTPBearer()


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
async def register(body: RegisterRequest) -> JSONResponse:
    if user_model.email_exists(body.email):
        raise HTTPException(status_code=409, detail="email_already_registered")

    hashed = hash_password(body.password)
    user = user_model.create(body.email, hashed)
    token = create_token(user["id"], user["email"])

    return JSONResponse(
        {"token": token, "user_id": user["id"], "email": user["email"]}, status_code=201
    )


@router.post("/login")
async def login(body: LoginRequest) -> JSONResponse:
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
