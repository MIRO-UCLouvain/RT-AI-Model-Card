"""Unit tests for services/publication.py state machine.

Uses asyncio.run() + unittest.mock — no real database required.
"""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from services.publication import (
    _SUBMITTABLE,
    approve_version,
    reject_version,
    request_publication,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ver(status: str, owner_id: uuid.UUID | None = None) -> MagicMock:
    v = MagicMock()
    v.status = status
    v.version = "v1.0"
    v.model_card = MagicMock()
    v.model_card.owner_id = owner_id or uuid.uuid4()
    return v


def _user(is_admin: bool = False, uid: uuid.UUID | None = None) -> MagicMock:
    u = MagicMock()
    u.id = uid or uuid.uuid4()
    u.is_admin = is_admin
    return u


def _session() -> AsyncMock:
    s = AsyncMock()
    s.commit = AsyncMock()
    return s


def _run(coro):
    return asyncio.run(coro)


# ── _SUBMITTABLE constant ─────────────────────────────────────────────────────

def test_submittable_contains_draft_and_rejected() -> None:
    assert _SUBMITTABLE == {"draft", "rejected"}


def test_in_review_not_submittable() -> None:
    assert "in_review" not in _SUBMITTABLE


def test_published_not_submittable() -> None:
    assert "published" not in _SUBMITTABLE


# ── request_publication ───────────────────────────────────────────────────────

@patch("services.publication.ModelCardVersionRepository.get_by_id")
def test_submit_draft_transitions_to_in_review(mock_get) -> None:
    owner_id = uuid.uuid4()
    ver = _ver("draft", owner_id)
    mock_get.return_value = ver

    _run(request_publication(_session(), 1, _user(uid=owner_id)))

    assert ver.status == "in_review"


@patch("services.publication.ModelCardVersionRepository.get_by_id")
def test_submit_rejected_transitions_to_in_review(mock_get) -> None:
    owner_id = uuid.uuid4()
    ver = _ver("rejected", owner_id)
    mock_get.return_value = ver

    _run(request_publication(_session(), 1, _user(uid=owner_id)))

    assert ver.status == "in_review"


@patch("services.publication.ModelCardVersionRepository.get_by_id")
def test_submit_in_review_raises_409(mock_get) -> None:
    owner_id = uuid.uuid4()
    ver = _ver("in_review", owner_id)
    mock_get.return_value = ver

    with pytest.raises(HTTPException) as exc:
        _run(request_publication(_session(), 1, _user(uid=owner_id)))
    assert exc.value.status_code == 409


@patch("services.publication.ModelCardVersionRepository.get_by_id")
def test_submit_published_raises_409(mock_get) -> None:
    owner_id = uuid.uuid4()
    ver = _ver("published", owner_id)
    mock_get.return_value = ver

    with pytest.raises(HTTPException) as exc:
        _run(request_publication(_session(), 1, _user(uid=owner_id)))
    assert exc.value.status_code == 409


@patch("services.publication.ModelCardVersionRepository.get_by_id")
def test_submit_by_non_owner_raises_403(mock_get) -> None:
    ver = _ver("draft", uuid.uuid4())  # owned by some UUID
    mock_get.return_value = ver
    other_user = _user(uid=uuid.uuid4())  # different UUID

    with pytest.raises(HTTPException) as exc:
        _run(request_publication(_session(), 1, other_user))
    assert exc.value.status_code == 403


# ── approve_version ───────────────────────────────────────────────────────────

@patch("services.publication.ModelCardVersionRepository.get_by_id")
def test_approve_in_review_transitions_to_published(mock_get) -> None:
    ver = _ver("in_review")
    mock_get.return_value = ver
    admin = _user(is_admin=True)

    _run(approve_version(_session(), 1, admin))

    assert ver.status == "published"


@pytest.mark.parametrize("bad_status", ["draft", "rejected", "published"])
@patch("services.publication.ModelCardVersionRepository.get_by_id")
def test_approve_wrong_status_raises_409(mock_get, bad_status: str) -> None:
    ver = _ver(bad_status)
    mock_get.return_value = ver
    admin = _user(is_admin=True)

    with pytest.raises(HTTPException) as exc:
        _run(approve_version(_session(), 1, admin))
    assert exc.value.status_code == 409


@patch("services.publication.ModelCardVersionRepository.get_by_id")
def test_approve_by_non_admin_raises_403(mock_get) -> None:
    ver = _ver("in_review")
    mock_get.return_value = ver

    with pytest.raises(HTTPException) as exc:
        _run(approve_version(_session(), 1, _user(is_admin=False)))
    assert exc.value.status_code == 403


# ── reject_version ────────────────────────────────────────────────────────────

@patch("services.publication.ModelCardVersionRepository.get_by_id")
def test_reject_in_review_transitions_to_rejected(mock_get) -> None:
    ver = _ver("in_review")
    mock_get.return_value = ver
    admin = _user(is_admin=True)

    _run(reject_version(_session(), 1, admin))

    assert ver.status == "rejected"


@pytest.mark.parametrize("bad_status", ["draft", "rejected", "published"])
@patch("services.publication.ModelCardVersionRepository.get_by_id")
def test_reject_wrong_status_raises_409(mock_get, bad_status: str) -> None:
    ver = _ver(bad_status)
    mock_get.return_value = ver
    admin = _user(is_admin=True)

    with pytest.raises(HTTPException) as exc:
        _run(reject_version(_session(), 1, admin))
    assert exc.value.status_code == 409


@patch("services.publication.ModelCardVersionRepository.get_by_id")
def test_reject_by_non_admin_raises_403(mock_get) -> None:
    ver = _ver("in_review")
    mock_get.return_value = ver

    with pytest.raises(HTTPException) as exc:
        _run(reject_version(_session(), 1, _user(is_admin=False)))
    assert exc.value.status_code == 403
