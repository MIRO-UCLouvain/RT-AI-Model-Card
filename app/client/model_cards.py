"""HTTP client for the RT-ModelCard FastAPI backend.

Uses synchronous httpx (Streamlit is not async).
Base URL is read from the BACKEND_URL environment variable,
defaulting to http://localhost:8000.

All public functions raise BackendError on any failure so callers
can display a user-friendly message without crashing.
"""

from __future__ import annotations

import os

import httpx

try:
    import streamlit as st
    _streamlit_url: str = st.secrets.get("BACKEND_URL", "")
except Exception:
    _streamlit_url = ""

_env_url: str = os.environ.get("BACKEND_URL", "")
_raw_url: str = _streamlit_url or _env_url or "http://localhost:8000"

# Ensure the URL always has a protocol prefix
if _raw_url and not _raw_url.startswith(("http://", "https://")):
    _raw_url = "https://" + _raw_url

BACKEND_URL: str = _raw_url
_TIMEOUT: float = 10.0


class BackendError(Exception):
    """Raised when the backend is unavailable or returns an error response."""


def _client() -> httpx.Client:
    return httpx.Client(base_url=BACKEND_URL, timeout=_TIMEOUT)


def _raise_for_status(response: httpx.Response) -> None:
    """Raise BackendError with a clean message on non-2xx responses.

    FastAPI 422 validation errors return detail as a list of dicts;
    we extract the human-readable 'msg' fields instead of showing the raw repr.
    """
    if response.is_error:
        try:
            body = response.json()
            detail = body.get("detail", response.text)
            if isinstance(detail, list):
                # FastAPI validation error format: [{"msg": "...", ...}, ...]
                msgs = [
                    e.get("msg", str(e))
                    for e in detail
                    if isinstance(e, dict)
                ]
                detail = " | ".join(msgs) if msgs else response.text
        except Exception:  # noqa: BLE001
            detail = response.text
        raise BackendError(str(detail))


# ── Auth ──────────────────────────────────────────────────────────────────────

def login(email: str, password: str) -> dict:
    """Authenticate and return ``{"access_token": ..., "token_type": "bearer"}``.

    The login endpoint uses OAuth2 form data; ``email`` maps to the
    ``username`` field as per the backend convention.
    """
    try:
        with _client() as client:
            response = client.post(
                "/v1/auth/login",
                data={"username": email, "password": password},
            )
        _raise_for_status(response)
        return response.json()  # type: ignore[no-any-return]
    except httpx.ConnectError:
        raise BackendError("Cannot reach backend — is it running?")
    except httpx.TimeoutException:
        raise BackendError("Request timed out. Try again.")


def register(email: str, password: str, first_name: str, last_name: str) -> dict:
    """Register a new user account. Returns the UserResponse dict."""
    try:
        with _client() as client:
            response = client.post(
                "/v1/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )
        _raise_for_status(response)
        return response.json()  # type: ignore[no-any-return]
    except httpx.ConnectError:
        raise BackendError("Cannot reach backend — is it running?")
    except httpx.TimeoutException:
        raise BackendError("Request timed out. Try again.")


def forgot_password(email: str) -> dict:
    """Request a password reset link for *email*.

    Always returns a dict with a ``message`` key.
    The same response is returned whether or not the email is registered,
    so callers must display the message verbatim without interpreting it.
    """
    try:
        with _client() as client:
            response = client.post(
                "/v1/auth/forgot-password",
                json={"email": email},
            )
        _raise_for_status(response)
        return response.json()  # type: ignore[no-any-return]
    except httpx.ConnectError:
        raise BackendError("Cannot reach backend — is it running?")
    except httpx.TimeoutException:
        raise BackendError("Request timed out. Try again.")


def reset_password(token: str, new_password: str) -> dict:
    """Submit a password reset using *token* from the reset email.

    Returns a dict with a ``message`` key on success.
    Raises BackendError with a user-friendly message on any failure.
    """
    try:
        with _client() as client:
            response = client.post(
                "/v1/auth/reset-password",
                json={"token": token, "new_password": new_password},
            )
        _raise_for_status(response)
        return response.json()  # type: ignore[no-any-return]
    except httpx.ConnectError:
        raise BackendError("Cannot reach backend — is it running?")
    except httpx.TimeoutException:
        raise BackendError("Request timed out. Try again.")


def get_me(token: str) -> dict:
    """Return the current user's profile (first_name, last_name, email, …)."""
    try:
        with _client() as client:
            response = client.get(
                "/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
        _raise_for_status(response)
        return response.json()  # type: ignore[no-any-return]
    except httpx.ConnectError:
        raise BackendError("Cannot reach backend — is it running?")
    except httpx.TimeoutException:
        raise BackendError("Request timed out. Try again.")


# ── Model cards ───────────────────────────────────────────────────────────────

def create_model_card(
    slug: str,
    task_type: str,
    title: str,
    user_version: str,
    content: dict,
    token: str = "",
) -> dict:
    """Create a new model card with its first version.

    ``user_version`` is the version string from the card form (e.g. "v1.0").
    Returns the full model card dict (id, slug, versions, …).
    Raises BackendError if the request fails or the backend is unreachable.
    """
    payload = {
        "slug": slug,
        "task_type": task_type,
        "first_version": {
            "title": title,
            "user_version": user_version,
            "content": content,
        },
    }
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        with _client() as client:
            response = client.post("/v1/model-cards", json=payload, headers=headers)
        _raise_for_status(response)
        return response.json()  # type: ignore[no-any-return]
    except httpx.ConnectError:
        raise BackendError("Cannot reach backend — is it running?")
    except httpx.TimeoutException:
        raise BackendError("Request timed out. Try again.")


def list_model_cards(token: str = "") -> list[dict]:
    """Return all model cards (with versions) owned by the authenticated user.

    Raises BackendError if the request fails.
    """
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        with _client() as client:
            response = client.get("/v1/model-cards", headers=headers)
        _raise_for_status(response)
        return response.json()  # type: ignore[no-any-return]
    except httpx.ConnectError:
        raise BackendError("Cannot reach backend — is it running?")
    except httpx.TimeoutException:
        raise BackendError("Request timed out. Try again.")


def get_versions(card_id: int) -> list[dict]:
    """Return all versions of a model card ordered by version_number.

    Raises BackendError if the request fails or the card does not exist.
    """
    try:
        with _client() as client:
            response = client.get(f"/v1/model-cards/{card_id}/versions")
        _raise_for_status(response)
        return response.json()  # type: ignore[no-any-return]
    except httpx.ConnectError:
        raise BackendError("Cannot reach backend — is it running?")
    except httpx.TimeoutException:
        raise BackendError("Request timed out. Try again.")


def create_version(
    card_id: int, title: str, user_version: str, content: dict, token: str = ""
) -> dict:
    """Save a new version of an existing model card.

    ``user_version`` is the version string from the card form (e.g. "v1.0").
    Returns the new version dict (id, version_number, is_latest, …).
    Raises BackendError if the request fails or the card does not exist.
    """
    payload = {"title": title, "user_version": user_version, "content": content}
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        with _client() as client:
            response = client.post(
                f"/v1/model-cards/{card_id}/versions", json=payload, headers=headers
            )
        _raise_for_status(response)
        return response.json()  # type: ignore[no-any-return]
    except httpx.ConnectError:
        raise BackendError("Cannot reach backend — is it running?")
    except httpx.TimeoutException:
        raise BackendError("Request timed out. Try again.")


def compare_versions(card_id: int, old_id: int, new_id: int) -> dict:
    """Compare two versions of a model card.

    Returns a DiffResponse dict with keys:
      old_version_id, new_version_id, old_version, new_version, sections.
    Each section has: added, removed, changed lists.
    """
    try:
        with _client() as client:
            response = client.get(
                f"/v1/model-cards/{card_id}/versions/compare",
                params={"old_id": old_id, "new_id": new_id},
            )
        _raise_for_status(response)
        return response.json()  # type: ignore[no-any-return]
    except httpx.ConnectError:
        raise BackendError("Cannot reach backend — is it running?")
    except httpx.TimeoutException:
        raise BackendError("Request timed out. Try again.")


def request_publication(card_id: int, version_id: int, token: str) -> dict:
    """Submit a specific version for publication review.

    Requires a valid Bearer token for the card owner.
    Returns the updated ModelCardVersionRead dict with status = 'in_review'.
    """
    try:
        with _client() as client:
            response = client.post(
                f"/v1/model-cards/{card_id}/versions/{version_id}/submit",
                headers={"Authorization": f"Bearer {token}"},
            )
        _raise_for_status(response)
        return response.json()  # type: ignore[no-any-return]
    except httpx.ConnectError:
        raise BackendError("Cannot reach backend — is it running?")
    except httpx.TimeoutException:
        raise BackendError("Request timed out. Try again.")


def delete_model_card(card_id: int, token: str) -> None:
    """Delete a model card and all its versions.

    Raises BackendError if the card is not found, the caller is not the owner,
    or the backend is unreachable.
    """
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with _client() as client:
            response = client.delete(
                f"/v1/model-cards/{card_id}",
                headers=headers,
            )
        _raise_for_status(response)
    except httpx.ConnectError:
        raise BackendError("Cannot reach backend — is it running?")
    except httpx.TimeoutException:
        raise BackendError("Request timed out. Try again.")


def get_public_version(version_id: int) -> dict:
    """Return full content of a published model card version.

    Raises BackendError if the version does not exist or is not published.
    """
    try:
        with _client() as client:
            response = client.get(f"/v1/public-model-cards/{version_id}")
        _raise_for_status(response)
        return response.json()  # type: ignore[no-any-return]
    except httpx.ConnectError:
        raise BackendError("Cannot reach backend — is it running?")
    except httpx.TimeoutException:
        raise BackendError("Request timed out. Try again.")


def list_public_model_cards() -> list[dict]:
    """Return summaries of all approved (published) model cards.

    No authentication required.
    """
    try:
        with _client() as client:
            response = client.get("/v1/public-model-cards")
        _raise_for_status(response)
        return response.json()  # type: ignore[no-any-return]
    except httpx.ConnectError:
        raise BackendError("Cannot reach backend — is it running?")
    except httpx.TimeoutException:
        raise BackendError("Request timed out. Try again.")
