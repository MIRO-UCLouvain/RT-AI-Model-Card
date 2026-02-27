"""Auth persistence utilities.

Stores JWT token and saved-card state in browser cookies so they survive
full page reloads (which happen when users click HTML <a href> topbar links
and reset Streamlit session state). On every page load, restore_auth() and
restore_card_state() read the cookies back into session state before any
rendering happens.

Cookie security notes
---------------------
- **HttpOnly is intentionally NOT set.**  Streamlit reads cookies via
  ``st.context.cookies``, which relies on ``document.cookie`` access on the
  client side.  Setting ``HttpOnly`` would make the cookie invisible to
  JavaScript and break the entire auth-persistence mechanism.  This is a
  fundamental limitation of Streamlit's architecture.
- **Secure flag** is set when the app is served over HTTPS (i.e. in
  production on Streamlit Cloud / Railway).  This prevents the JWT cookie
  from being transmitted over plain HTTP.
- **SameSite=Lax** is set on all cookies, which provides reasonable CSRF
  protection for top-level navigations while allowing the app to work
  correctly with Streamlit's iframe-based component model.
- **Server-side logout tracking** (``_logged_out_tokens``) prevents replay
  attacks from stale browser cookies that haven't been cleared yet by the
  asynchronous JS cookie-clearing.
- **Token sanitisation** (``_safe()``) strips quotes and semicolons to
  prevent cookie injection attacks.
"""

from __future__ import annotations

from urllib.parse import quote, unquote

import streamlit as st
import streamlit.components.v1 as components

from app.services.state_store import clear_form_state

_COOKIE_TOKEN = "rtmc_auth_token"
_COOKIE_EMAIL = "rtmc_auth_email"
_COOKIE_FIRST_NAME = "rtmc_auth_first_name"
_COOKIE_LAST_NAME = "rtmc_auth_last_name"
_COOKIE_CARD_ID = "rtmc_saved_card_id"
_COOKIE_CARD_VER = "rtmc_saved_version"
_COOKIE_CARD_SLUG = "rtmc_saved_slug"
_COOKIE_CARD_STATUS = "rtmc_saved_status"
_COOKIE_MAX_AGE = 3600  # 1 hour — matches JWT expiry

# Detect HTTPS context for the Secure cookie flag.  In production (Streamlit
# Cloud, Railway) the app is always served over HTTPS; locally it is HTTP.
# We check for common indicators rather than hard-coding.
import os as _os  # noqa: E402

_IS_HTTPS: bool = bool(
    _os.environ.get("STREAMLIT_SERVER_ENABLE_CORS")  # Streamlit Cloud sets this
    or _os.environ.get("RAILWAY_ENVIRONMENT")         # Railway sets this
    or _os.environ.get("HTTPS", "").lower() == "true"
)
_SECURE_FLAG: str = "Secure;" if _IS_HTTPS else ""

# Server-side set of tokens that have been explicitly logged out.
# Persists across Streamlit reruns and full-page reloads within the same
# server process, so stale browser cookies can never re-authenticate a
# logged-out token even before the JS cookie-clearing has executed.
_logged_out_tokens: set[str] = set()


def _js_set(*pairs: tuple[str, str], max_age: int = _COOKIE_MAX_AGE) -> str:
    """Build the JS cookie-setting lines for the given name=value pairs.

    Writes to ``window.parent.document.cookie`` so the cookie is set on the
    Streamlit page itself, not on the (sandboxed, soon-to-be-removed) component
    iframe.  Falls back to ``document.cookie`` if cross-frame access is blocked.
    """
    lines = "\n".join(
        f'try {{ window.parent.document.cookie="{name}={value};path=/;SameSite=Lax;{_SECURE_FLAG}max-age={max_age}"; }}'
        f' catch (e) {{ document.cookie="{name}={value};path=/;SameSite=Lax;{_SECURE_FLAG}max-age={max_age}"; }}'
        for name, value in pairs
    )
    return f"<script>{lines}</script>"


def _js_clear(*names: str) -> str:
    """Build JS cookie-clearing lines (max-age=0) for the given names."""
    lines = "\n".join(
        f'try {{ window.parent.document.cookie="{name}=;path=/;{_SECURE_FLAG}max-age=0"; }}'
        f' catch (e) {{ document.cookie="{name}=;path=/;{_SECURE_FLAG}max-age=0"; }}'
        for name in names
    )
    return f"<script>{lines}</script>"


def _inject(js_html: str) -> None:
    """Inject a JS-containing HTML string as a 0-height component."""
    components.html(js_html, height=0)


def _safe(value: str) -> str:
    """Encode a value so it survives a cookie round-trip in any browser.

    Per RFC 6265, cookie values must not contain spaces, commas, semicolons,
    quotes, or non-ASCII characters without quoting — and many browsers
    silently REJECT the entire ``Set-Cookie`` write when those characters
    appear unencoded.  This was the source of the "old account" auth bug:
    accounts whose ``first_name`` / ``last_name`` / ``email`` contained
    accented characters, spaces, or commas (common for non-English users
    and for anyone registered before the registration form normalised
    input) wrote the JWT cookie as a no-op, so the very next full-page
    reload (clicking "My Account" / "Contact support") found no cookie
    and bounced back to the login screen.

    URL-encoding the value side-steps the entire RFC restriction, and
    ``_decode_cookie()`` reverses it on read.
    """
    return quote(value, safe="")


def _decode_cookie(value: str | None) -> str | None:
    """Reverse the percent-encoding applied by ``_safe()`` on cookie write.

    Tolerant of legacy cookies that were stored unencoded (or with the
    older partial-strip ``_safe``): ``unquote`` is a no-op when no
    ``%XX`` escapes are present, so already-decoded values pass through
    unchanged.
    """
    if value is None:
        return None
    try:
        return unquote(value)
    except Exception:  # noqa: BLE001
        return value


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


def save_auth_and_redirect(
    token: str,
    email: str,
    first_name: str | None = None,
    last_name: str | None = None,
    *,
    redirect_url: str = "?view=home",
) -> None:
    """Persist auth state, fire-and-forget cookie writes, then navigate.

    Session state is set immediately so the very next Streamlit run sees
    the user as logged in — that is what drives the visible page change.
    Cookies are written via a components.html iframe (best-effort, for
    surviving full page reloads), but we do NOT depend on the iframe's
    JS to navigate: that path was unreliable in practice (hidden-iframe
    lazy loading, race with Streamlit's rerun), leaving users stuck on
    the auth screen even though authentication had succeeded.

    Navigation itself is driven by the caller through
    ``st.query_params + st.rerun()`` so the UI always transitions
    immediately on success.
    """
    st.session_state.auth_token = token
    st.session_state.auth_email = email
    st.session_state.auth_first_name = first_name or ""
    st.session_state.auth_last_name = last_name or ""
    # Clear any stale "logged out" guard so restore_auth() on the next
    # full page reload is allowed to rehydrate from cookies.
    st.session_state.pop("_auth_logged_out", None)
    # Discard the redirect_url's view= component into query_params here
    # so that callers who simply `st.rerun()` after us land on the right
    # page even if they forget to set query_params themselves.
    if redirect_url.startswith("?view="):
        st.query_params["view"] = redirect_url.split("=", 1)[1]

    pairs = (
        (_COOKIE_TOKEN, _safe(token)),
        (_COOKIE_EMAIL, _safe(email)),
        (_COOKIE_FIRST_NAME, _safe(first_name or "")),
        (_COOKIE_LAST_NAME, _safe(last_name or "")),
    )
    _inject(_js_set(*pairs))


def _read_cookie(name: str) -> str | None:
    """Best-effort cookie read.

    Tries ``st.context.cookies`` first (populated from the initial HTTP request
    headers), then falls back to parsing the raw ``Cookie`` header from
    ``st.context.headers``.  Either path can be empty on the very first render
    after a full-page reload depending on Streamlit's internal timing, so we
    try both before giving up.
    """
    try:
        value = st.context.cookies.get(name)
        if value:
            return value
    except (AttributeError, KeyError):
        pass
    try:
        raw = st.context.headers.get("Cookie") or st.context.headers.get("cookie")
        if not raw:
            return None
        for part in raw.split(";"):
            k, _, v = part.strip().partition("=")
            if k == name:
                return v or None
    except (AttributeError, KeyError):
        pass
    return None


def restore_auth() -> None:
    """Restore auth from browser cookie if session state was reset by a page reload."""
    if st.session_state.get("auth_token"):
        return
    if st.session_state.get("_auth_logged_out"):
        return
    token = _decode_cookie(_read_cookie(_COOKIE_TOKEN))
    email = _decode_cookie(_read_cookie(_COOKIE_EMAIL))
    if token and email:
        # Never restore a token that was explicitly logged out in this
        # server process — guards against stale browser cookies when the
        # JS cookie-clearing hasn't fired before the next page reload.
        if token in _logged_out_tokens:
            return
        st.session_state.auth_token = token
        st.session_state.auth_email = email
        st.session_state.auth_first_name = _decode_cookie(_read_cookie(_COOKIE_FIRST_NAME)) or ""
        st.session_state.auth_last_name = _decode_cookie(_read_cookie(_COOKIE_LAST_NAME)) or ""


def clear_auth() -> None:
    """Clear auth from session state and expire browser cookies."""
    # The logout topbar link is a plain <a href> which causes a full page
    # reload.  That creates a *new* Streamlit session whose session_state has
    # no auth_token yet — so we fall back to reading the cookie directly.
    token = st.session_state.get("auth_token")
    if not token:
        try:
            token = _decode_cookie(st.context.cookies.get(_COOKIE_TOKEN))
        except AttributeError:
            pass
    if token:
        _logged_out_tokens.add(token)
    # ── Auth state ──────────────────────────────────────────────────────
    st.session_state.auth_token = None
    st.session_state.auth_email = None
    st.session_state.auth_first_name = None
    st.session_state.auth_last_name = None
    st.session_state.auth_is_admin = False
    st.session_state["_auth_logged_out"] = True
    # Profile fields added later
    for k in ("auth_institution", "auth_country"):
        st.session_state.pop(k, None)

    # ── Card / version state ─────────────────────────────────────────
    st.session_state.saved_card_id = None
    st.session_state.saved_version = None
    st.session_state.saved_version_id = None
    st.session_state.saved_version_status = None
    st.session_state.pop("saved_slug", None)

    # ── Submission dialog / diff state ───────────────────────────────
    for k in (
        "_pending_submit_card_id",
        "_pending_submit_ver_id",
        "_pending_submit_author_name",
        "_pending_submit_author_email",
        "_show_submit_dialog",
        "_diff_before_submit",
        "_diff_result",
        "_feedback_sent",
        "_my_cards_section",
        "_settings_section",
    ):
        st.session_state.pop(k, None)

    # ── Upload registries ────────────────────────────────────────────
    for k in (
        "render_uploads",
        "appendix_uploads",
        "all_uploaded_paths",
        "appendix_uploader_nonce",
        "normalized_uploads",
    ):
        st.session_state.pop(k, None)

    # ── Form data ────────────────────────────────────────────────────
    clear_form_state()
    _inject(_js_clear(
        _COOKIE_TOKEN, _COOKIE_EMAIL, _COOKIE_FIRST_NAME, _COOKIE_LAST_NAME,
        _COOKIE_CARD_ID, _COOKIE_CARD_VER, _COOKIE_CARD_SLUG, _COOKIE_CARD_STATUS,
    ))


# ── Card state ────────────────────────────────────────────────────────────────

def save_card_state(card_id: int, version: str, slug: str, status: str) -> None:
    """Persist saved-card identifiers in browser cookies for cross-reload recovery."""
    _inject(_js_set(
        (_COOKIE_CARD_ID, str(card_id)),
        (_COOKIE_CARD_VER, str(version)),
        (_COOKIE_CARD_SLUG, _safe(slug)),
        (_COOKIE_CARD_STATUS, _safe(status)),
    ))


def clear_card_state() -> None:
    """Clear card-related session state and expire the card browser cookies.

    Also sets a one-shot guard flag so that the very next call to
    restore_card_state() skips cookie restoration, preventing stale cookies
    from immediately re-hydrating the state we just cleared (which would
    happen because JS cookie-clearing is asynchronous with respect to the
    next Streamlit rerun).
    """
    for key in ("saved_card_id", "saved_version", "saved_version_id",
                "saved_version_status", "saved_slug"):
        st.session_state.pop(key, None)
    st.session_state["_new_card_mode"] = True
    _inject(_js_clear(
        _COOKIE_CARD_ID, _COOKIE_CARD_VER, _COOKIE_CARD_SLUG, _COOKIE_CARD_STATUS,
    ))


def restore_card_state() -> None:
    """Restore saved-card state from browser cookies after a page reload.

    Skips restoration if ``saved_card_id`` is already in session state, or if
    ``_new_card_mode`` is set (consumed on first check so it fires exactly once).
    """
    if st.session_state.get("saved_card_id"):
        return
    # Guard: clear_card_state() sets this to prevent cookie restoration
    # until the JS cookie-clearing has had time to execute.
    if st.session_state.get("_new_card_mode"):
        # Check if cookies are actually gone yet
        if not _read_cookie(_COOKIE_CARD_ID):
            st.session_state.pop("_new_card_mode", None)
        return
    try:
        card_id_str = _decode_cookie(_read_cookie(_COOKIE_CARD_ID))
        version_str = _decode_cookie(_read_cookie(_COOKIE_CARD_VER))
        slug = _decode_cookie(_read_cookie(_COOKIE_CARD_SLUG))
        status = _decode_cookie(_read_cookie(_COOKIE_CARD_STATUS))
        if card_id_str and version_str:
            st.session_state.saved_card_id = int(card_id_str)
            st.session_state.saved_version = version_str
            if slug:
                st.session_state.saved_slug = slug
            if status:
                st.session_state.saved_publication_status = status
    except ValueError:
        pass
