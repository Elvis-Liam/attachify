"""Authentication endpoints: register, login, refresh, Google sign-in, forgot/reset password, delete account."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.security import create_token, decode_token, hash_password
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    ForgotPasswordRequest,
    GoogleAuthRequest,
    RefreshRequest,
    ResetPasswordRequest,
    TokenPair,
    UserLogin,
    UserOut,
    UserRegister,
)
from app.services.auth_service import AuthService
from app.services.email_service import get_email_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)) -> User:
    return await AuthService(db).register(data)


@router.post("/login", response_model=TokenPair)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)) -> TokenPair:
    service = AuthService(db)
    user = await service.authenticate(data)
    return service.issue_tokens(user)


@router.post("/refresh", response_model=TokenPair)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    return await AuthService(db).refresh_access_token(data.refresh_token)


@router.post("/google", response_model=TokenPair)
async def google_login(data: GoogleAuthRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    """Verify a Google ID token from the client and log in or create the matching user."""
    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Google sign-in isn't configured yet.")

    try:
        claims = google_id_token.verify_oauth2_token(
            data.id_token, google_requests.Request(), settings.google_client_id
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Google token.") from exc

    repo = UserRepository(db)
    user = await repo.get_by_google_id(claims["sub"])
    if user is None:
        user = await repo.get_by_email(claims["email"])
        if user is not None:
            user.google_id = claims["sub"]
        else:
            user = User(
                email=claims["email"],
                google_id=claims["sub"],
                full_name=claims.get("name", claims["email"]),
                is_verified=claims.get("email_verified", False),
            )
            db.add(user)
        await db.commit()
        await db.refresh(user)

    return AuthService(db).issue_tokens(user)


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Always responds the same way regardless of whether the email exists, so this
    endpoint can't be used to enumerate registered accounts."""
    user = await UserRepository(db).get_by_email(data.email)
    if user is not None:
        reset_token = create_token(user.id, "access")
        await get_email_service().send(
            to=user.email,
            subject="Reset your Attachify password",
            body=f"Use this token to reset your password: {reset_token}",
        )
    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    try:
        payload = decode_token(data.token)
    except Exception as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired reset token.") from exc

    repo = UserRepository(db)
    user = await repo.get_by_id(uuid.UUID(payload["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired reset token.")

    user.password_hash = hash_password(data.new_password)
    await db.commit()
    return {"message": "Password updated."}


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await AuthService(db).delete_account(current_user)
