"""Shared FastAPI dependencies — the current authenticated user, derived from a bearer JWT."""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_error = HTTPException(status.HTTP_401_UNAUTHORIZED, "Could not validate credentials.")
    try:
        payload = decode_token(credentials.credentials)
    except Exception as exc:
        raise credentials_error from exc

    if payload.get("type") != "access":
        raise credentials_error

    user = await UserRepository(db).get_by_id(uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise credentials_error
    return user
