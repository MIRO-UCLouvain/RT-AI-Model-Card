"""Pydantic schemas for the feedback / contact form."""

from pydantic import BaseModel, EmailStr, Field


class FeedbackRequest(BaseModel):
    email: EmailStr
    topic: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    message: str = Field(min_length=10)
    page_context: str = ""


class FeedbackResponse(BaseModel):
    message: str
