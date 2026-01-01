"""Tests for the password reset service layer.

All database I/O is mocked at the repository level so these tests run
without a live database or SMTP server.

Coverage targets (per the specification):
 1. forgot-password with existing email → generic success, token created
 2. forgot-password with non-existing email → same generic success, no token
 3. token stored with hashed value, NOT the raw token
 4. reset succeeds with valid token
 5. reset fails with expired token
 6. reset fails with already-used token
 7. reset fails with invalid/unknown token
 8. successful reset updates the stored password hash
 9. token cannot be reused after a successful reset
10. older active tokens are invalidated when a new token is requested
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_USER_ID = uuid.uuid4()


def _make_user(
    *,
    email: str = "user@example.com",
    hashed_password: str = "old_hash",
    is_active: bool = True,
) -> MagicMock:
    user = MagicMock()
    user.id = _USER_ID
    user.email = email
    user.hashed_password = hashed_password
    user.is_active = is_active
    return user


def _make_token_record(
    *,
    raw_token: str,
    user_id: uuid.UUID = _USER_ID,
    expired: bool = False,
    used: bool = False,
) -> MagicMock:
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    record = MagicMock()
    record.user_id = user_id
    record.token_hash = token_hash
    record.expires_at = (
        datetime.now(UTC) - timedelta(hours=1)
        if expired
        else datetime.now(UTC) + timedelta(hours=1)
    )
    record.used_at = datetime.now(UTC) if used else None
    return record


# ---------------------------------------------------------------------------
# Test: request_password_reset
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_forgot_password_existing_email_returns_silently() -> None:
    """request_password_reset completes without raising for a known email."""
    session = AsyncMock()
    user = _make_user()

    with (
        patch(
            "services.password_reset.UserRepository.get_by_email",
            new=AsyncMock(return_value=user),
        ),
        patch(
            "services.password_reset.PasswordResetRepository"
            ".invalidate_active_tokens_for_user",
            new=AsyncMock(),
        ),
        patch(
            "services.password_reset.PasswordResetRepository.create",
            new=AsyncMock(),
        ),
        patch(
            "services.password_reset.send_password_reset_email",
            new=AsyncMock(),
        ),
    ):
        # Must not raise
        from services.password_reset import request_password_reset

        await request_password_reset(session, "user@example.com")


@pytest.mark.asyncio
async def test_forgot_password_unknown_email_returns_silently() -> None:
    """request_password_reset completes without raising for an unknown email.

    No token creation or email sending should occur.
    """
    session = AsyncMock()

    create_mock = AsyncMock()
    send_mock = AsyncMock()

    with (
        patch(
            "services.password_reset.UserRepository.get_by_email",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "services.password_reset.PasswordResetRepository.create",
            new=create_mock,
        ),
        patch(
            "services.password_reset.send_password_reset_email",
            new=send_mock,
        ),
    ):
        from services.password_reset import request_password_reset

        await request_password_reset(session, "nobody@example.com")

    create_mock.assert_not_called()
    send_mock.assert_not_called()


@pytest.mark.asyncio
async def test_forgot_password_stores_token_hash_not_raw() -> None:
    """The value stored in the DB must be the SHA-256 hash, never the raw token."""
    session = AsyncMock()
    user = _make_user()
    stored_calls: list[dict] = []

    async def _capture_create(
        _session: object,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> MagicMock:
        stored_calls.append({"token_hash": token_hash})
        return MagicMock()

    with (
        patch(
            "services.password_reset.UserRepository.get_by_email",
            new=AsyncMock(return_value=user),
        ),
        patch(
            "services.password_reset.PasswordResetRepository"
            ".invalidate_active_tokens_for_user",
            new=AsyncMock(),
        ),
        patch(
            "services.password_reset.PasswordResetRepository.create",
            new=_capture_create,
        ),
        patch(
            "services.password_reset.send_password_reset_email",
            new=AsyncMock(),
        ),
        patch("services.password_reset.secrets.token_urlsafe", return_value="raw_tok"),
    ):
        from services.password_reset import request_password_reset

        await request_password_reset(session, "user@example.com")

    assert len(stored_calls) == 1
    stored_hash = stored_calls[0]["token_hash"]
    expected_hash = hashlib.sha256("raw_tok".encode("utf-8")).hexdigest()
    # Stored value must equal the SHA-256 digest
    assert stored_hash == expected_hash
    # Stored value must NOT be the raw token
    assert stored_hash != "raw_tok"


@pytest.mark.asyncio
async def test_forgot_password_invalidates_previous_active_tokens() -> None:
    """Requesting a reset invalidates all existing active tokens for the user."""
    session = AsyncMock()
    user = _make_user()
    invalidate_mock = AsyncMock()

    with (
        patch(
            "services.password_reset.UserRepository.get_by_email",
            new=AsyncMock(return_value=user),
        ),
        patch(
            "services.password_reset.PasswordResetRepository"
            ".invalidate_active_tokens_for_user",
            new=invalidate_mock,
        ),
        patch(
            "services.password_reset.PasswordResetRepository.create",
            new=AsyncMock(),
        ),
        patch(
            "services.password_reset.send_password_reset_email",
            new=AsyncMock(),
        ),
    ):
        from services.password_reset import request_password_reset

        await request_password_reset(session, "user@example.com")

    invalidate_mock.assert_awaited_once()
    # First arg (after session) must be the correct user_id
    assert invalidate_mock.await_args[0][1] == _USER_ID


# ---------------------------------------------------------------------------
# Test: reset_password
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reset_password_valid_token_succeeds() -> None:
    """A valid token causes the user password to be updated."""
    session = AsyncMock()
    raw_token = "valid_raw_token"
    user = _make_user()
    token_record = _make_token_record(raw_token=raw_token)

    new_hash_value = "new_bcrypt_hash"

    with (
        patch(
            "services.password_reset.PasswordResetRepository.get_valid_by_hash",
            new=AsyncMock(return_value=token_record),
        ),
        patch(
            "services.password_reset.UserRepository.get_by_id",
            new=AsyncMock(return_value=user),
        ),
        patch(
            "services.password_reset.PasswordResetRepository"
            ".invalidate_active_tokens_for_user",
            new=AsyncMock(),
        ),
        patch(
            "services.password_reset.hash_password",
            return_value=new_hash_value,
        ),
    ):
        from services.password_reset import reset_password

        await reset_password(session, raw_token, "new_secure_pass")

    assert user.hashed_password == new_hash_value


@pytest.mark.asyncio
async def test_reset_password_updates_stored_hash() -> None:
    """After reset, the hashed_password on the user object reflects the new value."""
    session = AsyncMock()
    raw_token = "tok"
    user = _make_user(hashed_password="old_bcrypt_hash")
    token_record = _make_token_record(raw_token=raw_token)

    with (
        patch(
            "services.password_reset.PasswordResetRepository.get_valid_by_hash",
            new=AsyncMock(return_value=token_record),
        ),
        patch(
            "services.password_reset.UserRepository.get_by_id",
            new=AsyncMock(return_value=user),
        ),
        patch(
            "services.password_reset.PasswordResetRepository"
            ".invalidate_active_tokens_for_user",
            new=AsyncMock(),
        ),
        patch(
            "services.password_reset.hash_password",
            return_value="brand_new_hash",
        ),
    ):
        from services.password_reset import reset_password

        await reset_password(session, raw_token, "newpassword1")

    assert user.hashed_password == "brand_new_hash"
    assert user.hashed_password != "old_bcrypt_hash"


@pytest.mark.asyncio
async def test_reset_password_invalid_token_raises_400() -> None:
    """An unknown / non-existent token must raise HTTP 400."""
    from fastapi import HTTPException

    session = AsyncMock()

    with patch(
        "services.password_reset.PasswordResetRepository.get_valid_by_hash",
        new=AsyncMock(return_value=None),
    ):
        from services.password_reset import reset_password

        with pytest.raises(HTTPException) as exc_info:
            await reset_password(session, "bogus_token", "newpassword1")

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_reset_password_expired_token_raises_400() -> None:
    """An expired token returns None from the repository and raises HTTP 400.

    The repository already filters out expired tokens; the service receives
    None and must treat it identically to an unknown token.
    """
    from fastapi import HTTPException

    session = AsyncMock()

    # Repository returns None (expired tokens are filtered at query time)
    with patch(
        "services.password_reset.PasswordResetRepository.get_valid_by_hash",
        new=AsyncMock(return_value=None),
    ):
        from services.password_reset import reset_password

        with pytest.raises(HTTPException) as exc_info:
            await reset_password(session, "expired_token", "newpassword1")

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_reset_password_used_token_raises_400() -> None:
    """An already-used token returns None from the repository and raises HTTP 400.

    The repository already filters out used tokens; the service receives
    None and must treat it identically to an unknown token.
    """
    from fastapi import HTTPException

    session = AsyncMock()

    with patch(
        "services.password_reset.PasswordResetRepository.get_valid_by_hash",
        new=AsyncMock(return_value=None),
    ):
        from services.password_reset import reset_password

        with pytest.raises(HTTPException) as exc_info:
            await reset_password(session, "used_token", "newpassword1")

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_reset_password_invalidates_all_tokens_on_success() -> None:
    """After a successful reset, invalidate_active_tokens is called for the user."""
    session = AsyncMock()
    raw_token = "tok"
    user = _make_user()
    token_record = _make_token_record(raw_token=raw_token)
    invalidate_mock = AsyncMock()

    with (
        patch(
            "services.password_reset.PasswordResetRepository.get_valid_by_hash",
            new=AsyncMock(return_value=token_record),
        ),
        patch(
            "services.password_reset.UserRepository.get_by_id",
            new=AsyncMock(return_value=user),
        ),
        patch(
            "services.password_reset.PasswordResetRepository"
            ".invalidate_active_tokens_for_user",
            new=invalidate_mock,
        ),
        patch("services.password_reset.hash_password", return_value="h"),
    ):
        from services.password_reset import reset_password

        await reset_password(session, raw_token, "newpassword1")

    invalidate_mock.assert_awaited_once()
    assert invalidate_mock.await_args[0][1] == _USER_ID


@pytest.mark.asyncio
async def test_reset_password_token_cannot_be_reused() -> None:
    """The second reset attempt with the same token must raise 400.

    After a successful reset the repository returns None for that token hash
    because ``used_at`` is now set.  The service must raise 400.
    """
    from fastapi import HTTPException

    session = AsyncMock()
    raw_token = "reuse_me"
    user = _make_user()
    token_record = _make_token_record(raw_token=raw_token)

    call_count = 0

    async def _get_valid_by_hash(
        _session: object, _hash: str
    ) -> MagicMock | None:
        nonlocal call_count
        call_count += 1
        # First call: valid; subsequent calls: None (token now used)
        if call_count == 1:
            return token_record
        return None

    with (
        patch(
            "services.password_reset.PasswordResetRepository.get_valid_by_hash",
            new=_get_valid_by_hash,
        ),
        patch(
            "services.password_reset.UserRepository.get_by_id",
            new=AsyncMock(return_value=user),
        ),
        patch(
            "services.password_reset.PasswordResetRepository"
            ".invalidate_active_tokens_for_user",
            new=AsyncMock(),
        ),
        patch("services.password_reset.hash_password", return_value="h"),
    ):
        from services.password_reset import reset_password

        # First use succeeds
        await reset_password(session, raw_token, "newpassword1")

        # Second use must raise
        with pytest.raises(HTTPException) as exc_info:
            await reset_password(session, raw_token, "anotherpassword1")

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_smtp_error_does_not_propagate_to_caller() -> None:
    """An SMTP failure must be swallowed; request_password_reset must not raise."""
    session = AsyncMock()
    user = _make_user()

    with (
        patch(
            "services.password_reset.UserRepository.get_by_email",
            new=AsyncMock(return_value=user),
        ),
        patch(
            "services.password_reset.PasswordResetRepository"
            ".invalidate_active_tokens_for_user",
            new=AsyncMock(),
        ),
        patch(
            "services.password_reset.PasswordResetRepository.create",
            new=AsyncMock(),
        ),
        patch(
            "services.password_reset.send_password_reset_email",
            new=AsyncMock(side_effect=ConnectionRefusedError("SMTP down")),
        ),
    ):
        from services.password_reset import request_password_reset

        # Must not raise even though email delivery failed
        await request_password_reset(session, "user@example.com")


@pytest.mark.asyncio
async def test_reset_password_deleted_user_raises_400() -> None:
    """If the user has been deleted after the token was created, raise HTTP 400."""
    from fastapi import HTTPException

    session = AsyncMock()
    raw_token = "orphan_tok"
    token_record = _make_token_record(raw_token=raw_token)

    with (
        patch(
            "services.password_reset.PasswordResetRepository.get_valid_by_hash",
            new=AsyncMock(return_value=token_record),
        ),
        patch(
            "services.password_reset.UserRepository.get_by_id",
            new=AsyncMock(return_value=None),  # user deleted
        ),
    ):
        from services.password_reset import reset_password

        with pytest.raises(HTTPException) as exc_info:
            await reset_password(session, raw_token, "newpassword1")

    assert exc_info.value.status_code == 400
