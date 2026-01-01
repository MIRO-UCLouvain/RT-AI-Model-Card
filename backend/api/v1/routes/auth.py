"""Authentication routes — registration, login, profile, and password reset."""

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_current_user, get_db
from models.user import User
from schemas.password_reset import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from schemas.user import TokenResponse, UserCreate, UserResponse
from security import create_access_token
from services.password_reset import request_password_reset, reset_password
from services.user import authenticate_user, create_user

router = APIRouter(prefix="/auth", tags=["auth"])

_FORGOT_PASSWORD_RESPONSE = (
    "If an account with that email exists, a reset link has been sent."
)


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
    return TokenResponse(
        access_token=token,
        first_name=user.first_name,
        last_name=user.last_name,
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> ForgotPasswordResponse:
    """Request a password reset link.

    Always returns the same generic message to prevent email enumeration.
    """
    await request_password_reset(db, data.email)
    return ForgotPasswordResponse(message=_FORGOT_PASSWORD_RESPONSE)


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password_endpoint(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> ResetPasswordResponse:
    """Apply a password reset using the token from the reset email.

    Raises 400 if the token is invalid, expired, or already used.
    """
    await reset_password(db, data.token, data.new_password)
    return ResetPasswordResponse(message="Your password has been reset successfully.")
