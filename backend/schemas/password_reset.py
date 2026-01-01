"""Pydantic schemas for the forgot-password / reset-password flow."""

from pydantic import BaseModel, EmailStr, Field


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    # Minimum 8 characters — same lower bound as UserCreate.password.
    new_password: str = Field(min_length=8)


class ResetPasswordResponse(BaseModel):
    message: str
