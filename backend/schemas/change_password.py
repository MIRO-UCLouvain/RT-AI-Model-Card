"""Pydantic schemas for the change-password flow (authenticated users)."""

from pydantic import BaseModel, Field


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


class ChangePasswordResponse(BaseModel):
    message: str
