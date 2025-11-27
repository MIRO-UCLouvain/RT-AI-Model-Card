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

BACKEND_URL: str = os.environ.get("BACKEND_URL", "http://localhost:8000")
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
    content: dict,
) -> dict:
    """Create a new model card with its first version.

    Returns the full model card dict (id, slug, versions, …).
    Raises BackendError if the request fails or the backend is unreachable.
    """
    payload = {
        "slug": slug,
        "task_type": task_type,
        "first_version": {
            "title": title,
            "content_json": content,
        },
    }
    try:
        with _client() as client:
            response = client.post("/v1/model-cards", json=payload)
        _raise_for_status(response)
        return response.json()  # type: ignore[no-any-return]
    except httpx.ConnectError:
        raise BackendError("Cannot reach backend — is it running?")
    except httpx.TimeoutException:
        raise BackendError("Request timed out. Try again.")


def list_model_cards() -> list[dict]:
    """Return all model card summaries.

    Raises BackendError if the request fails.
    """
    try:
        with _client() as client:
            response = client.get("/v1/model-cards")
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


def create_version(card_id: int, title: str, content: dict) -> dict:
    """Save a new version of an existing model card.

    Returns the new version dict (id, version_number, is_latest, …).
    Raises BackendError if the request fails or the card does not exist.
    """
    payload = {"title": title, "content_json": content}
    try:
        with _client() as client:
            response = client.post(
                f"/v1/model-cards/{card_id}/versions", json=payload
            )
        _raise_for_status(response)
        return response.json()  # type: ignore[no-any-return]
    except httpx.ConnectError:
        raise BackendError("Cannot reach backend — is it running?")
    except httpx.TimeoutException:
        raise BackendError("Request timed out. Try again.")


def request_publication(card_id: int, token: str) -> dict:
    """Submit a model card for publication review.

    Requires a valid Bearer token for the card owner.
    Returns the updated model card dict with publication_status = 'pending'.
    """
    try:
        with _client() as client:
            response = client.post(
                f"/v1/model-cards/{card_id}/request-publication",
                headers={"Authorization": f"Bearer {token}"},
            )
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
