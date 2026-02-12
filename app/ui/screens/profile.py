"""Account Settings screen — unified profile + security at ?view=profile."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.client.model_cards import BackendError, change_password
from app.ui.utils.auth import clear_auth
from app.ui.utils.css import inject_css

AUTH_CSS = Path(__file__).resolve().parent.parent / "static" / "auth.css"

# Inline SVG — settings/cog icon (Feather-style)
_SETTINGS_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
    '<circle cx="12" cy="12" r="3"/>'
    '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 '
    '2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 '
    '2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06'
    '.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 '
    '0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 '
    '0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 '
    '4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 '
    '1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 '
    '1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 '
    '1.65 0 0 0-1.51 1z"/>'
    '</svg>'
)


def _validate_password_change(
    current: str, new: str, confirm: str,
) -> str | None:
    """Return an error message or None if inputs are valid."""
    if not current:
        return "Please enter your current password."
    if not new:
        return "Please enter a new password."
    if len(new) < 8:
        return "New password must be at least 8 characters."
    if new != confirm:
        return "New passwords do not match."
    if current == new:
        return "New password must be different from the current one."
    return None


def profile_page() -> None:
    """Render the unified Account Settings page."""
    if not st.session_state.get("auth_token"):
        st.warning("You must be logged in to view your profile.")
        st.markdown("[Login](?view=login)", unsafe_allow_html=True)
        return

    inject_css(AUTH_CSS)

    email: str = st.session_state.get("auth_email", "")
    first_name: str = st.session_state.get("auth_first_name", "")
    last_name: str = st.session_state.get("auth_last_name", "")

    if first_name and last_name:
        display_name = f"{first_name} {last_name}"
    elif first_name:
        display_name = first_name
    elif last_name:
        display_name = last_name
    else:
        display_name = email.split("@")[0] if email else ""

    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        with st.container(border=True):
            # ── Card header ─────────────────────────────────────────
            st.markdown(
                '<div class="auth-header">'
                f'<div class="auth-header__icon">{_SETTINGS_SVG}</div>'
                '<h2 class="auth-header__title">Account Settings</h2>'
                '<p class="auth-header__subtitle">'
                'Manage your profile and security preferences'
                '</p>'
                '</div>',
                unsafe_allow_html=True,
            )

            # ── Profile / Security tabs ─────────────────────────────
            tab_profile, tab_security = st.tabs(["Profile", "Security"])

            # ── Tab 1: Profile ──────────────────────────────────────
            with tab_profile:
                st.markdown(
                    '<div class="profile-info">'
                    '<div class="profile-info__row">'
                    '<span class="profile-info__label">Name</span>'
                    f'<span class="profile-info__value">{display_name}</span>'
                    '</div>'
                    '<div class="profile-info__row">'
                    '<span class="profile-info__label">Email</span>'
                    f'<span class="profile-info__value">{email}</span>'
                    '</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            # ── Tab 2: Security ─────────────────────────────────────
            with tab_security:
                st.markdown(
                    '<p class="settings-section__helper">'
                    'Choose a strong password with at least 8 characters. '
                    'We recommend mixing letters, numbers, and symbols.'
                    '</p>',
                    unsafe_allow_html=True,
                )

                with st.form("form_change_password"):
                    current_pw = st.text_input(
                        "Current password",
                        type="password",
                        key="cp_current",
                        placeholder="Enter your current password",
                    )
                    new_pw = st.text_input(
                        "New password",
                        type="password",
                        key="cp_new",
                        placeholder="At least 8 characters",
                    )
                    confirm_pw = st.text_input(
                        "Confirm new password",
                        type="password",
                        key="cp_confirm",
                        placeholder="Re-enter your new password",
                    )
                    submitted = st.form_submit_button(
                        "Update password", use_container_width=True,
                    )

                if submitted:
                    error = _validate_password_change(
                        current_pw, new_pw, confirm_pw,
                    )
                    if error:
                        st.error(error)
                    else:
                        token = st.session_state.get("auth_token", "")
                        try:
                            result = change_password(token, current_pw, new_pw)
                            st.success(
                                result.get(
                                    "message",
                                    "Password changed successfully.",
                                )
                            )
                        except BackendError as exc:
                            st.error(str(exc))

            # ── Sign out (bottom, less prominent) ───────────────────
            st.markdown(
                '<div class="settings-signout-divider"></div>',
                unsafe_allow_html=True,
            )
            if st.button(
                "Sign out",
                key="profile_logout",
                use_container_width=True,
            ):
                clear_auth()
                st.query_params["view"] = "home"
                st.rerun()

    _, col_back, _ = st.columns([1, 2, 1])
    with col_back:
        if st.button(
            "\u2190 Back to Main Page",
            key="profile_back_home",
            use_container_width=True,
        ):
            st.query_params["view"] = "home"
            st.rerun()
