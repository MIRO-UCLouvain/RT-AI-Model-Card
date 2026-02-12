"""Feedback / contact form route."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from dependencies import get_db
from models.user import User
from repositories.user import UserRepository
from schemas.feedback import FeedbackRequest, FeedbackResponse
from security import verify_token
from services.email import send_email

router = APIRouter(prefix="/feedback", tags=["feedback"])
logger = logging.getLogger(__name__)


async def _resolve_user(
    db: AsyncSession,
    authorization: str | None,
) -> User | None:
    """Best-effort user resolution from an optional Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        token = authorization.removeprefix("Bearer ")
        user_id = verify_token(token)
        return await UserRepository.get_by_id(db, user_id)
    except Exception:
        return None


def _build_feedback_email(
    data: FeedbackRequest,
    user: User | None,
) -> tuple[str, str, str]:
    """Return (subject, body_plain, body_html) for a feedback submission."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    subject = f"[AID-RT Model Card Feedback] {data.topic} — {data.subject}"

    user_line = ""
    user_html = ""
    if user:
        name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        user_line = f"User ID: {user.id}\nName: {name}\n"
        user_html = (
            '<tr><td style="padding:6px 12px;color:#64748b;font-weight:600;">User</td>'
            f'<td style="padding:6px 12px;">{name} ({user.id})</td></tr>'
        )

    page_line = ""
    page_html = ""
    if data.page_context:
        page_line = f"Page: {data.page_context}\n"
        page_html = (
            '<tr><td style="padding:6px 12px;color:#64748b;font-weight:600;">Page</td>'
            f'<td style="padding:6px 12px;">{data.page_context}</td></tr>'
        )

    body_plain = (
        f"New feedback submission\n"
        f"{'=' * 40}\n\n"
        f"From: {data.email}\n"
        f"Topic: {data.topic}\n"
        f"Subject: {data.subject}\n"
        f"{user_line}"
        f"{page_line}"
        f"Timestamp: {now}\n\n"
        f"Message:\n{'-' * 40}\n"
        f"{data.message}\n"
    )

    body_html = f"""\
<html>
<body style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:32px 16px;">
  <h2 style="color:#1e293b;margin:0 0 8px;">New feedback submission</h2>
  <p style="color:#64748b;font-size:0.875rem;margin:0 0 24px;">Received {now}</p>
  <table style="width:100%;border-collapse:collapse;font-size:0.9rem;margin-bottom:24px;">
    <tr style="background:#f8fafc;">
      <td style="padding:6px 12px;color:#64748b;font-weight:600;">From</td>
      <td style="padding:6px 12px;">{data.email}</td>
    </tr>
    <tr>
      <td style="padding:6px 12px;color:#64748b;font-weight:600;">Topic</td>
      <td style="padding:6px 12px;">{data.topic}</td>
    </tr>
    <tr style="background:#f8fafc;">
      <td style="padding:6px 12px;color:#64748b;font-weight:600;">Subject</td>
      <td style="padding:6px 12px;">{data.subject}</td>
    </tr>
    {user_html}
    {page_html}
  </table>
  <div style="background:#f8fafc;border-left:3px solid #2563eb;padding:16px 20px;border-radius:4px;">
    <p style="color:#64748b;font-size:0.8rem;margin:0 0 8px;font-weight:600;">MESSAGE</p>
    <p style="color:#1e293b;margin:0;white-space:pre-wrap;line-height:1.6;">{data.message}</p>
  </div>
</body>
</html>"""

    return subject, body_plain, body_html


@router.post(
    "",
    response_model=FeedbackResponse,
    status_code=status.HTTP_200_OK,
)
async def submit_feedback(
    data: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> FeedbackResponse:
    """Accept a feedback submission and email it to the admin.

    Authentication is optional — if a valid Bearer token is present the
    user's identity is included in the email for context.
    """
    user = await _resolve_user(db, authorization)
    subject, body_plain, body_html = _build_feedback_email(data, user)

    try:
        sent = await send_email(
            recipient_email=settings.FEEDBACK_EMAIL,
            subject=subject,
            body_plain=body_plain,
            body_html=body_html,
        )
    except Exception:
        logger.exception("Failed to send feedback email from %s", data.email)
        return FeedbackResponse(
            message="Your feedback was received but we could not send the notification email. "
            "Please try again later or contact us directly."
        )

    logger.info("Feedback submitted by %s — topic: %s", data.email, data.topic)
    if not sent:
        return FeedbackResponse(
            message="No email provider is configured. "
            "Please set RESEND_API_KEY or SMTP_HOST in the environment to enable email delivery."
        )
    return FeedbackResponse(message="Thanks — your feedback has been sent.")
