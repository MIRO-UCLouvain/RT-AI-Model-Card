"""Login screen — polished centered card at ?view=login with User / Administrator tabs."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.client.model_cards import BackendError, get_me, login
from app.ui.utils.auth import save_auth_and_redirect
from app.ui.utils.css import inject_css

AUTH_CSS = Path(__file__).resolve().parent.parent / "static" / "auth.css"

# Inline SVG — lock icon (Feather-style)
_LOCK_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
    '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>'
    '<path d="M7 11V7a5 5 0 0 1 10 0v4"/>'
    '</svg>'
)


def _attempt_login(
    email: str, password: str, *, admin_mode: bool
) -> tuple[tuple[str, str, str, str] | None, bool]:
    """Validate credentials and check role.

    Returns ``(auth_result_tuple | None, is_admin)``.
    """
    if not email or not password:
        st.error("Please enter your email and password.")
        return None, False

    try:
        result = login(email.strip(), password)
    except BackendError as exc:
        st.error(str(exc))
        return None, False

    token = result["access_token"]
    first_name = result.get("first_name") or ""
    last_name = result.get("last_name") or ""
    is_admin = False

    try:
        profile = get_me(token)
        first_name = profile.get("first_name") or first_name
        last_name = profile.get("last_name") or last_name
        is_admin = bool(profile.get("is_admin", False))
    except BackendError:
        pass

    if admin_mode and not is_admin:
        st.error("This account does not have administrator privileges.")
        return None, False

    return (token, email.strip(), first_name, last_name), is_admin


def login_page() -> None:
    """Render the polished login card with User / Administrator tabs."""
    inject_css(AUTH_CSS)

    _auth_result: tuple[str, str, str, str] | None = None
    _is_admin: bool = False

    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        with st.container(border=True):
            # ── Header ───────────────────────────────────────────────────
            st.markdown(
                '<div class="auth-header">'
                f'<div class="auth-header__icon">{_LOCK_SVG}</div>'
                '<h2 class="auth-header__title">Welcome back</h2>'
                '<p class="auth-header__subtitle">Sign in to your account</p>'
                '</div>',
                unsafe_allow_html=True,
            )

            # ── Tabs ─────────────────────────────────────────────────────
            tab_user, tab_admin = st.tabs(["User", "Administrator"])

            with tab_user:
                with st.form("form_login_user"):
                    email_u = st.text_input(
                        "Email", key="login_user_email",
                        placeholder="you@example.com",
                    )
                    pass_u = st.text_input(
                        "Password", type="password", key="login_user_pass",
                        placeholder="Enter your password",
                    )
                    submitted_u = st.form_submit_button(
                        "Sign in", use_container_width=True
                    )
                if submitted_u:
                    _auth_result, _is_admin = _attempt_login(
                        email_u, pass_u, admin_mode=False
                    )

            with tab_admin:
                with st.form("form_login_admin"):
                    email_a = st.text_input(
                        "Email", key="login_admin_email",
                        placeholder="admin@example.com",
                    )
                    pass_a = st.text_input(
                        "Password", type="password", key="login_admin_pass",
                        placeholder="Enter your password",
                    )
                    submitted_a = st.form_submit_button(
                        "Sign in as Administrator", use_container_width=True
                    )
                if submitted_a:
                    _auth_result, _is_admin = _attempt_login(
                        email_a, pass_a, admin_mode=True
                    )

            # ── Footer ───────────────────────────────────────────────────
            st.markdown(
                '<div class="auth-footer">'
                "Don't have an account? "
                "<a href='?view=register'>Create one</a>"
                '</div>',
                unsafe_allow_html=True,
            )

    # Set auth cookies then navigate.
    if _auth_result:
        st.session_state.auth_is_admin = _is_admin
        target = "admin" if _is_admin else "home"
        save_auth_and_redirect(*_auth_result, redirect_url=f"?view={target}")
        st.query_params["view"] = target
        st.rerun()

    _, col_back, _ = st.columns([1, 2, 1])
    with col_back:
        if st.button("← Back to Main Page", key="login_back_home", use_container_width=True):
            st.query_params["view"] = "home"
            st.rerun()
