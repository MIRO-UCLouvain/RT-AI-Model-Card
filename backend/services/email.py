"""Outbound email service.

Abstraction over SMTP so callers never deal with transport details directly.
All SMTP settings come from ``config.settings`` — swap them in the environment
to change providers without touching code.

Development shortcut:
  Set ``SMTP_HOST=""`` (the default) to skip sending entirely.
  When ``DEBUG=true``, the reset URL is logged at INFO level so you can test
  the flow locally without a real mail server.
"""

import asyncio
import json
import logging
import smtplib
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import partial

from config import settings

logger = logging.getLogger(__name__)


def _build_message(
    recipient_email: str,
    reset_url: str,
    expiry_minutes: int,
) -> MIMEMultipart:
    """Construct the reset-password MIME message."""
    subject = "Reset your RT-ModelCard password"

    body_plain = (
        "Password reset request\n\n"
        "We received a request to reset the password for your RT-ModelCard "
        "account.\n\n"
        f"Open this link to choose a new password "
        f"(expires in {expiry_minutes} minutes):\n"
        f"{reset_url}\n\n"
        "If you did not request this, you can safely ignore this email — "
        "your password will not change."
    )

    body_html = f"""\
<html>
<body style="font-family:sans-serif;max-width:560px;margin:0 auto;padding:32px 16px;">
  <h2 style="color:#1e293b;">Password reset request</h2>
  <p style="color:#475569;">
    We received a request to reset the password for your RT-ModelCard account.
  </p>
  <p style="color:#475569;">
    Click the button below to choose a new password.
    This link expires in <strong>{expiry_minutes} minutes</strong>.
  </p>
  <p style="text-align:center;margin:36px 0;">
    <a href="{reset_url}"
       style="background:#2563eb;color:#ffffff;padding:13px 32px;
              border-radius:6px;text-decoration:none;font-weight:600;
              font-size:1rem;display:inline-block;">
      Reset my password
    </a>
  </p>
  <p style="color:#64748b;font-size:0.875rem;">
    If the button above does not work, paste this URL into your browser:
  </p>
  <p style="word-break:break-all;color:#64748b;font-size:0.875rem;">
    {reset_url}
  </p>
  <hr style="margin:40px 0;border:none;border-top:1px solid #e2e8f0;" />
  <p style="color:#94a3b8;font-size:0.8rem;">
    If you did not request a password reset, you can safely ignore this email.
    Your password will not be changed.
  </p>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = recipient_email
    msg.attach(MIMEText(body_plain, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))
    return msg


def _send_via_resend(
    recipient_email: str,
    subject: str,
    body_plain: str,
    body_html: str,
) -> None:
    """Send email via Resend HTTP API (blocking — run inside a thread executor)."""
    payload = json.dumps({
        "from": settings.EMAIL_FROM,
        "to": [recipient_email],
        "subject": subject,
        "text": body_plain,
        "html": body_html,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        if resp.status not in (200, 201):
            raise RuntimeError(f"Resend API returned {resp.status}")


def _send_sync(msg: MIMEMultipart, recipient_email: str) -> None:
    """Send *msg* via SMTP (blocking — run inside a thread executor)."""
    host = settings.SMTP_HOST
    port = settings.SMTP_PORT
    username = settings.SMTP_USERNAME or None
    password = settings.SMTP_PASSWORD or None

    if settings.SMTP_USE_TLS:
        smtp_cls: smtplib.SMTP = smtplib.SMTP_SSL(host, port)
    else:
        smtp_cls = smtplib.SMTP(host, port)

    with smtp_cls as smtp:
        if settings.SMTP_START_TLS and not settings.SMTP_USE_TLS:
            smtp.starttls()
        if username and password:
            smtp.login(username, password)
        smtp.sendmail(settings.EMAIL_FROM, [recipient_email], msg.as_string())


async def send_password_reset_email(
    *,
    recipient_email: str,
    reset_url: str,
    expiry_minutes: int,
) -> None:
    """Send a password reset email asynchronously.

    The raw token appears only inside *reset_url* and is never logged.

    If ``SMTP_HOST`` is empty (default dev configuration) the send is skipped
    and, when ``DEBUG`` is true, the reset URL is logged at INFO level.

    Any SMTP error is re-raised so the caller can decide whether to
    propagate it or swallow it.
    """
    if not settings.RESEND_API_KEY and not settings.SMTP_HOST:
        if settings.DEBUG:
            logger.warning(
                "SMTP not configured — DEV reset URL for %s: %s",
                recipient_email,
                reset_url,
            )
        else:
            logger.warning(
                "No email provider configured; reset email not sent to %s",
                recipient_email,
            )
        return

    msg = _build_message(recipient_email, reset_url, expiry_minutes)
    loop = asyncio.get_event_loop()

    if settings.RESEND_API_KEY:
        # Extract parts from the already-built message for Resend API
        subject = msg["Subject"]
        parts = {p.get_content_type(): p.get_payload(decode=True).decode("utf-8") for p in msg.get_payload()}  # type: ignore[union-attr]
        await loop.run_in_executor(
            None,
            partial(
                _send_via_resend,
                recipient_email,
                subject,
                parts.get("text/plain", ""),
                parts.get("text/html", ""),
            ),
        )
    else:
        await loop.run_in_executor(None, partial(_send_sync, msg, recipient_email))

    logger.info("Password reset email sent to %s", recipient_email)
