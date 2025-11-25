"""Authentication routes — registration and login."""

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db
from schemas.user import TokenResponse, UserCreate, UserResponse
from security import create_access_token
from services.user import authenticate_user, create_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new user account."""
    user = await create_user(db, data)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate and return a Bearer JWT.

    The ``username`` field of the OAuth2 form is treated as the user's email.
    """
    user = await authenticate_user(db, form.username, form.password)
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)
