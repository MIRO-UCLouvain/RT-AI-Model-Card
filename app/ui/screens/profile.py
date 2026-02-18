"""Account Settings screen — unified profile + security at ?view=profile."""

from __future__ import annotations

from pathlib import Path

import re

import streamlit as st

from app.client.model_cards import BackendError, change_password, submit_feedback
from app.ui.utils.auth import clear_auth
from app.ui.utils.css import inject_css

_FEEDBACK_TOPICS = [
    "General feedback",
    "Bug report",
    "Feature request",
    "UX / interface",
    "Login / account",
    "Model basic information",
    "Clinical problem",
    "Intended use",
    "Training data",
    "Validation data",
    "Model performance",
    "Limitations",
    "Ethical considerations",
    "Publication workflow",
    "PDF export",
    "Other",
]

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

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

            # ── Profile / Security / Feedback tabs ─────────────────
            tab_profile, tab_security, tab_feedback = st.tabs(
                ["Profile", "Security", "Feedback"],
            )

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

            # ── Tab 3: Feedback ─────────────────────────────────────
            with tab_feedback:
                if st.session_state.get("_feedback_sent"):
                    st.markdown(
                        '<div style="text-align:center;padding:1.5rem 0.5rem;">'
                        '<div style="font-size:2.5rem;margin-bottom:0.4rem;">&#9993;</div>'
                        '<p style="font-size:1.15rem;font-weight:700;margin:0 0 6px;'
                        'color:var(--ink,#1e293b);">Feedback sent!</p>'
                        '<p style="color:var(--muted,#64748b);font-size:0.9rem;'
                        'margin:0;line-height:1.5;">'
                        'Thank you for writing to us. We will review your '
                        'message and get back to you if needed.'
                        '</p>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "Send another",
                        use_container_width=True,
                        key="fb_another",
                    ):
                        del st.session_state["_feedback_sent"]
                        st.rerun()
                else:
                    st.markdown(
                        '<p class="settings-section__helper">'
                        'Send feedback, report a bug, or request a feature.'
                        '</p>',
                        unsafe_allow_html=True,
                    )

                    fb_email = st.text_input(
                        "Email address *",
                        value=email,
                        placeholder="you@example.com",
                        key="fb_email",
                    )
                    fb_topic = st.selectbox(
                        "Topic *",
                        options=_FEEDBACK_TOPICS,
                        index=0,
                        key="fb_topic",
                    )
                    fb_subject = st.text_input(
                        "Subject *",
                        placeholder="Brief description of your feedback",
                        key="fb_subject",
                    )
                    fb_message = st.text_area(
                        "Message *",
                        placeholder="Tell us more…",
                        height=140,
                        key="fb_message",
                    )

                    if st.button(
                        "Send feedback",
                        use_container_width=True,
                        key="fb_submit",
                    ):
                        errors: list[str] = []
                        fb_email_v = (fb_email or "").strip()
                        fb_subject_v = (fb_subject or "").strip()
                        fb_message_v = (fb_message or "").strip()
                        fb_topic_v = fb_topic or ""

                        if not fb_email_v:
                            errors.append("Email address is required.")
                        elif not _EMAIL_RE.match(fb_email_v):
                            errors.append("Please enter a valid email address.")
                        if not fb_topic_v:
                            errors.append("Please select a topic.")
                        if not fb_subject_v:
                            errors.append("Subject is required.")
                        if not fb_message_v:
                            errors.append("Message is required.")
                        elif len(fb_message_v) < 10:
                            errors.append("Message must be at least 10 characters.")

                        if errors:
                            for err in errors:
                                st.error(err)
                        else:
                            token = st.session_state.get("auth_token") or ""
                            try:
                                with st.spinner("Sending your feedback…"):
                                    submit_feedback(
                                        email=fb_email_v,
                                        topic=fb_topic_v,
                                        subject=fb_subject_v,
                                        message=fb_message_v,
                                        token=token,
                                    )
                                for k in ("fb_email", "fb_topic",
                                          "fb_subject", "fb_message"):
                                    st.session_state.pop(k, None)
                                st.session_state["_feedback_sent"] = True
                                st.rerun()
                            except BackendError as exc:
                                st.error(f"Could not send feedback: {exc}")

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
