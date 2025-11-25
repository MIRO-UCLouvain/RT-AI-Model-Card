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
_COOKIE_CARD_ID = "rtmc_saved_card_id"
_COOKIE_CARD_VER = "rtmc_saved_version"
_COOKIE_CARD_SLUG = "rtmc_saved_slug"
_COOKIE_CARD_STATUS = "rtmc_saved_status"
_COOKIE_MAX_AGE = 3600  # 1 hour — matches JWT expiry


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


# ── Auth ──────────────────────────────────────────────────────────────────────

def save_auth(token: str, email: str) -> None:
    """Save auth state to session state and browser cookie."""
    safe_token = token.replace('"', "").replace("'", "").replace(";", "")
    safe_email = email.replace('"', "").replace("'", "").replace(";", "")
    st.session_state.auth_token = token
    st.session_state.auth_email = email
    _inject(_js_set((_COOKIE_TOKEN, safe_token), (_COOKIE_EMAIL, safe_email)))


def restore_auth() -> None:
    """Restore auth from browser cookie if session state was reset by a page reload.

    Call this at the very top of main() before any rendering.
    Skipped if the user explicitly logged out this session (_auth_logged_out flag).
    """
    if st.session_state.get("auth_token"):
        return
    if st.session_state.get("_auth_logged_out"):
        return  # User logged out this session — don't re-authenticate
    try:
        cookies = st.context.cookies  # available since Streamlit 1.34
        token = cookies.get(_COOKIE_TOKEN)
        email = cookies.get(_COOKIE_EMAIL)
        if token and email:
            st.session_state.auth_token = token
            st.session_state.auth_email = email
    except AttributeError:
        pass  # older Streamlit version without st.context.cookies


def clear_auth() -> None:
    """Clear auth from session state and expire browser cookies.

    Sets _auth_logged_out so restore_auth() won't re-read the cookies
    during the same WebSocket session (soft reruns). The actual cookie
    expiry JS runs in the browser asynchronously via a hidden iframe.
    Callers should follow with st.query_params["view"] = "home" + st.rerun().
    """
    st.session_state.auth_token = None
    st.session_state.auth_email = None
    st.session_state["_auth_logged_out"] = True
    # Also clear saved card state
    st.session_state.saved_card_id = None
    st.session_state.saved_version = None
    st.session_state.saved_publication_status = None
    _inject(_js_clear(_COOKIE_TOKEN, _COOKIE_EMAIL,
                      _COOKIE_CARD_ID, _COOKIE_CARD_VER,
                      _COOKIE_CARD_SLUG, _COOKIE_CARD_STATUS))


# ── Card state ────────────────────────────────────────────────────────────────

def save_card_state(card_id: int, version: int, slug: str, status: str) -> None:
    """Persist saved-card identifiers in browser cookies for cross-reload recovery."""
    safe_slug = slug.replace('"', "").replace("'", "").replace(";", "")
    safe_status = status.replace('"', "").replace("'", "").replace(";", "")
    _inject(_js_set(
        (_COOKIE_CARD_ID, str(card_id)),
        (_COOKIE_CARD_VER, str(version)),
        (_COOKIE_CARD_SLUG, safe_slug),
        (_COOKIE_CARD_STATUS, safe_status),
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
