"""Current-user endpoint, used by authenticated pages to show who's logged in."""
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.auth import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
