"""Unit tests for admin user management logic.

Tests the route handler functions directly with mocked repository calls.
No real database or HTTP server required.
"""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from api.v1.routes.admin_users import (
    activate_user,
    deactivate_user,
    grant_admin,
    list_users,
    revoke_admin,
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _user(
    is_admin: bool = False,
    is_active: bool = True,
    uid: uuid.UUID | None = None,
) -> MagicMock:
    u = MagicMock()
    u.id = uid or uuid.uuid4()
    u.email = "test@example.com"
    u.first_name = "Test"
    u.last_name = "User"
    u.is_admin = is_admin
    u.is_active = is_active
    u.institution = "Test U"
    u.country = "BE"
    u.created_at = "2026-01-01T00:00:00"
    return u


def _admin(uid: uuid.UUID | None = None) -> MagicMock:
    return _user(is_admin=True, uid=uid)


def _session() -> AsyncMock:
    s = AsyncMock()
    s.commit = AsyncMock()
    s.refresh = AsyncMock()
    return s


def _run(coro):  # type: ignore[no-untyped-def]
    return asyncio.run(coro)


# ── list_users ───────────────────────────────────────────────────────────────


@patch("api.v1.routes.admin_users.UserRepository.list_all")
def test_list_users_returns_all(mock_list) -> None:  # type: ignore[no-untyped-def]
    users = [_user(), _user(), _admin()]
    mock_list.return_value = users
    result = _run(list_users(db=_session(), _current_user=_admin()))
    assert len(result) == 3


# ── activate_user ────────────────────────────────────────────────────────────


@patch("api.v1.routes.admin_users.UserRepository.get_by_id")
def test_activate_user_sets_active_true(mock_get) -> None:  # type: ignore[no-untyped-def]
    target = _user(is_active=False)
    mock_get.return_value = target
    session = _session()
    _run(activate_user(target.id, db=session, _current_user=_admin()))
    assert target.is_active is True
    session.commit.assert_awaited_once()


# ── deactivate_user ──────────────────────────────────────────────────────────


@patch("api.v1.routes.admin_users.UserRepository.get_by_id")
def test_deactivate_user_sets_active_false(mock_get) -> None:  # type: ignore[no-untyped-def]
    target = _user(is_active=True)
    mock_get.return_value = target
    admin = _admin()
    session = _session()
    _run(deactivate_user(target.id, db=session, current_user=admin))
    assert target.is_active is False
    session.commit.assert_awaited_once()


@patch("api.v1.routes.admin_users.UserRepository.get_by_id")
def test_deactivate_self_raises_400(mock_get) -> None:  # type: ignore[no-untyped-def]
    admin = _admin()
    mock_get.return_value = admin
    with pytest.raises(HTTPException) as exc:
        _run(deactivate_user(admin.id, db=_session(), current_user=admin))
    assert exc.value.status_code == 400


@patch("api.v1.routes.admin_users.UserRepository.get_by_id")
def test_deactivate_nonexistent_user_raises_404(mock_get) -> None:  # type: ignore[no-untyped-def]
    mock_get.return_value = None
    admin = _admin()
    with pytest.raises(HTTPException) as exc:
        _run(deactivate_user(uuid.uuid4(), db=_session(), current_user=admin))
    assert exc.value.status_code == 404


# ── grant_admin ──────────────────────────────────────────────────────────────


@patch("api.v1.routes.admin_users.UserRepository.get_by_id")
def test_grant_admin_sets_is_admin_true(mock_get) -> None:  # type: ignore[no-untyped-def]
    target = _user(is_admin=False)
    mock_get.return_value = target
    session = _session()
    _run(grant_admin(target.id, db=session, _current_user=_admin()))
    assert target.is_admin is True
    session.commit.assert_awaited_once()


# ── revoke_admin ─────────────────────────────────────────────────────────────


@patch("api.v1.routes.admin_users.UserRepository.get_by_id")
def test_revoke_admin_sets_is_admin_false(mock_get) -> None:  # type: ignore[no-untyped-def]
    target = _admin()
    mock_get.return_value = target
    calling_admin = _admin()  # different admin
    session = _session()
    _run(revoke_admin(target.id, db=session, current_user=calling_admin))
    assert target.is_admin is False
    session.commit.assert_awaited_once()


@patch("api.v1.routes.admin_users.UserRepository.get_by_id")
def test_revoke_own_admin_raises_400(mock_get) -> None:  # type: ignore[no-untyped-def]
    admin = _admin()
    mock_get.return_value = admin
    with pytest.raises(HTTPException) as exc:
        _run(revoke_admin(admin.id, db=_session(), current_user=admin))
    assert exc.value.status_code == 400
