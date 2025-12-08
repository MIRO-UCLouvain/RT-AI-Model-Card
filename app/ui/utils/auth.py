"""Auth persistence utilities.

Stores JWT token and saved-card state in browser cookies so they survive
full page reloads (which happen when users click HTML <a href> topbar links
and reset Streamlit session state). On every page load, restore_auth() and
restore_card_state() read the cookies back into session state before any
rendering happens.
"""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

_COOKIE_TOKEN = "rtmc_auth_token"
_COOKIE_EMAIL = "rtmc_auth_email"
_COOKIE_FIRST_NAME = "rtmc_auth_first_name"
_COOKIE_LAST_NAME = "rtmc_auth_last_name"
_COOKIE_CARD_ID = "rtmc_saved_card_id"
_COOKIE_CARD_VER = "rtmc_saved_version"
_COOKIE_CARD_SLUG = "rtmc_saved_slug"
_COOKIE_CARD_STATUS = "rtmc_saved_status"
_COOKIE_MAX_AGE = 3600  # 1 hour — matches JWT expiry

# Server-side set of tokens that have been explicitly logged out.
# Persists across Streamlit reruns and full-page reloads within the same
# server process, so stale browser cookies can never re-authenticate a
# logged-out token even before the JS cookie-clearing has executed.
_logged_out_tokens: set[str] = set()


def _js_set(*pairs: tuple[str, str], max_age: int = _COOKIE_MAX_AGE) -> str:
    """Build the JS cookie-setting lines for the given name=value pairs."""
    lines = "\n".join(
        f'document.cookie="{name}={value};path=/;SameSite=Lax;max-age={max_age}";'
        for name, value in pairs
    )
    return f"<script>{lines}</script>"


def _js_clear(*names: str) -> str:
    """Build JS cookie-clearing lines (max-age=0) for the given names."""
    lines = "\n".join(
        f'document.cookie="{name}=;path=/;max-age=0";'
        for name in names
    )
    return f"<script>{lines}</script>"


def _inject(js_html: str) -> None:
    """Inject a JS-containing HTML string as a 0-height component."""
    components.html(js_html, height=0)


def _safe(value: str) -> str:
    """Strip characters that would break a cookie value."""
    return value.replace('"', "").replace("'", "").replace(";", "")


# ── Auth ──────────────────────────────────────────────────────────────────────

def save_auth(
    token: str,
    email: str,
    first_name: str | None = None,
    last_name: str | None = None,
) -> None:
    """Save auth state to session state and browser cookies."""
    st.session_state.auth_token = token
    st.session_state.auth_email = email
    st.session_state.auth_first_name = first_name or ""
    st.session_state.auth_last_name = last_name or ""

    pairs: list[tuple[str, str]] = [
        (_COOKIE_TOKEN, _safe(token)),
        (_COOKIE_EMAIL, _safe(email)),
        (_COOKIE_FIRST_NAME, _safe(first_name or "")),
        (_COOKIE_LAST_NAME, _safe(last_name or "")),
    ]
    _inject(_js_set(*pairs))


def restore_auth() -> None:
    """Restore auth from browser cookie if session state was reset by a page reload."""
    if st.session_state.get("auth_token"):
        return
    if st.session_state.get("_auth_logged_out"):
        return
    try:
        cookies = st.context.cookies
        token = cookies.get(_COOKIE_TOKEN)
        email = cookies.get(_COOKIE_EMAIL)
        if token and email:
            # Never restore a token that was explicitly logged out in this
            # server process — guards against stale browser cookies when the
            # JS cookie-clearing hasn't fired before the next page reload.
            if token in _logged_out_tokens:
                return
            st.session_state.auth_token = token
            st.session_state.auth_email = email
            st.session_state.auth_first_name = cookies.get(_COOKIE_FIRST_NAME, "")
            st.session_state.auth_last_name = cookies.get(_COOKIE_LAST_NAME, "")
    except AttributeError:
        pass


def clear_auth() -> None:
    """Clear auth from session state and expire browser cookies."""
    # The logout topbar link is a plain <a href> which causes a full page
    # reload.  That creates a *new* Streamlit session whose session_state has
    # no auth_token yet — so we fall back to reading the cookie directly.
    token = st.session_state.get("auth_token")
    if not token:
        try:
            token = st.context.cookies.get(_COOKIE_TOKEN)
        except AttributeError:
            pass
    if token:
        _logged_out_tokens.add(token)
    st.session_state.auth_token = None
    st.session_state.auth_email = None
    st.session_state.auth_first_name = None
    st.session_state.auth_last_name = None
    st.session_state["_auth_logged_out"] = True
    st.session_state.saved_card_id = None
    st.session_state.saved_version = None
    st.session_state.saved_publication_status = None
    _inject(_js_clear(
        _COOKIE_TOKEN, _COOKIE_EMAIL, _COOKIE_FIRST_NAME, _COOKIE_LAST_NAME,
        _COOKIE_CARD_ID, _COOKIE_CARD_VER, _COOKIE_CARD_SLUG, _COOKIE_CARD_STATUS,
    ))


# ── Card state ────────────────────────────────────────────────────────────────

def save_card_state(card_id: int, version: int, slug: str, status: str) -> None:
    """Persist saved-card identifiers in browser cookies for cross-reload recovery."""
    _inject(_js_set(
        (_COOKIE_CARD_ID, str(card_id)),
        (_COOKIE_CARD_VER, str(version)),
        (_COOKIE_CARD_SLUG, _safe(slug)),
        (_COOKIE_CARD_STATUS, _safe(status)),
    ))


def restore_card_state() -> None:
    """Restore saved-card state from browser cookies after a page reload."""
    if st.session_state.get("saved_card_id"):
        return
    try:
        cookies = st.context.cookies
        card_id_str = cookies.get(_COOKIE_CARD_ID)
        version_str = cookies.get(_COOKIE_CARD_VER)
        slug = cookies.get(_COOKIE_CARD_SLUG)
        status = cookies.get(_COOKIE_CARD_STATUS)
        if card_id_str and version_str:
            st.session_state.saved_card_id = int(card_id_str)
            st.session_state.saved_version = int(version_str)
            if slug:
                st.session_state.saved_slug = slug
            if status:
                st.session_state.saved_publication_status = status
    except (AttributeError, ValueError):
        pass
