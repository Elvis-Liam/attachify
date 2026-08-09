"""Business logic for registration, login, and token refresh."""
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_token, decode_token, hash_password, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenPair, UserLogin, UserRegister


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)

    async def register(self, data: UserRegister) -> User:
        existing = await self.users.get_by_email(data.email)
        if existing is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists.")

        user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            role=UserRole.STUDENT,
        )
        user = await self.users.create(user)
        await self.db.commit()
        return user

    async def authenticate(self, data: UserLogin) -> User:
        user = await self.users.get_by_email(data.email)
        if user is None or user.password_hash is None or not verify_password(data.password, user.password_hash):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password.")
        if not user.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been deactivated.")
        return user

    def issue_tokens(self, user: User) -> TokenPair:
        return TokenPair(
            access_token=create_token(user.id, "access"),
            refresh_token=create_token(user.id, "refresh"),
        )

    async def refresh_access_token(self, refresh_token: str) -> TokenPair:
        try:
            payload = decode_token(refresh_token)
        except Exception as exc:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token.") from exc

        if payload.get("type") != "refresh":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not a refresh token.")

        user = await self.users.get_by_id(uuid.UUID(payload["sub"]))
        if user is None or not user.is_active:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists or is inactive.")

        return self.issue_tokens(user)

    async def delete_account(self, user: User) -> None:
        await self.users.delete(user)
        await self.db.commit()
