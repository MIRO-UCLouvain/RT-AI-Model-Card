"""Account Settings screen — desktop sidebar layout at ?view=profile."""

from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

from app.client.model_cards import BackendError, change_password, get_me, submit_feedback
from app.ui.utils.auth import clear_auth, restore_auth
from app.ui.utils.css import inject_css

_FEEDBACK_TOPICS = [
    "General feedback",
    "Bug report",
    "Feature request",
    "UX / interface",
    "Login / account",
    "Model basic information",
    "Intended use",
    "Training data",
    "Validation data",
    "Limitations",
    "Ethical considerations",
    "Publication workflow",
    "PDF export",
    "Other",
]

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

AUTH_CSS = Path(__file__).resolve().parent.parent / "static" / "auth.css"
SETTINGS_CSS = Path(__file__).resolve().parent.parent / "static" / "settings.css"

_SECTIONS = [
    ("profile", "Profile"),
    ("security", "Change password"),
    ("feedback", "Contact"),
]


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


def _render_profile(
    display_name: str,
    email: str,
    initial: str,
    institution: str,
    country: str,
) -> None:
    """Render the Profile section."""
    st.markdown(
        '<div class="settings-section">'
        '<h3 class="settings-section__title">Profile</h3>'
        '<p class="settings-section__desc">Your account information</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown(
            f'<div class="profile-card">'
            f'<div class="profile-card__avatar">{initial}</div>'
            f'<div class="profile-card__info">'
            f'<div class="profile-card__name">{display_name}</div>'
            f'<div class="profile-card__email">{email}</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        inst_display = institution if institution else "—"
        country_display = country if country else "—"
        st.markdown(
            '<div class="profile-info">'
            '<div class="profile-info__row">'
            '<span class="profile-info__label">Full name</span>'
            f'<span class="profile-info__value">{display_name}</span>'
            '</div>'
            '<div class="profile-info__row">'
            '<span class="profile-info__label">Email address</span>'
            f'<span class="profile-info__value">{email}</span>'
            '</div>'
            '<div class="profile-info__row">'
            '<span class="profile-info__label">Institution</span>'
            f'<span class="profile-info__value">{inst_display}</span>'
            '</div>'
            '<div class="profile-info__row">'
            '<span class="profile-info__label">Country</span>'
            f'<span class="profile-info__value">{country_display}</span>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div style="margin-top:0.75rem;"></div>',
        unsafe_allow_html=True,
    )
    if st.button("Sign out", key="profile_signout", use_container_width=True):
        clear_auth()
        st.query_params["view"] = "home"
        st.rerun()


def _render_security() -> None:
    """Render the Security section."""
    st.markdown(
        '<div class="settings-section">'
        '<h3 class="settings-section__title">Security</h3>'
        '<p class="settings-section__desc">Update your password</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
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
            error = _validate_password_change(current_pw, new_pw, confirm_pw)
            if error:
                st.error(error)
            else:
                token = st.session_state.get("auth_token", "")
                try:
                    result = change_password(token, current_pw, new_pw)
                    st.success(
                        result.get("message", "Password changed successfully.")
                    )
                except BackendError as exc:
                    st.error(str(exc))


def _render_feedback(email: str) -> None:
    """Render the Feedback section."""
    st.markdown(
        '<div class="settings-section">'
        '<h3 class="settings-section__title">Feedback</h3>'
        '<p class="settings-section__desc">'
        'Send feedback, report a bug, or request a feature'
        '</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.get("_feedback_sent"):
        with st.container(border=True):
            st.markdown(
                '<div style="text-align:center;padding:2rem 1rem;">'
                '<div style="font-size:3rem;margin-bottom:0.5rem;">&#9993;</div>'
                '<p style="font-size:1.2rem;font-weight:700;margin:0 0 8px;'
                'color:var(--ink,#1e293b);">Feedback sent!</p>'
                '<p style="color:var(--muted,#64748b);font-size:0.9rem;'
                'margin:0 0 20px;line-height:1.5;">'
                'Thank you for writing to us. We will review your '
                'message and get back to you if needed.'
                '</p>'
                '</div>',
                unsafe_allow_html=True,
            )
            if st.button("Send another", use_container_width=True, key="fb_another"):
                del st.session_state["_feedback_sent"]
                st.rerun()
        return

    with st.container(border=True):
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
            height=160,
            key="fb_message",
        )

        if st.button("Send feedback", use_container_width=True, key="fb_submit"):
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
                    for k in ("fb_email", "fb_topic", "fb_subject", "fb_message"):
                        st.session_state.pop(k, None)
                    st.session_state["_feedback_sent"] = True
                    st.rerun()
                except BackendError as exc:
                    st.error(f"Could not send feedback: {exc}")


def profile_page() -> None:
    """Render the Account Settings page with sidebar navigation."""
    if not st.session_state.get("auth_token"):
        # Last-chance cookie restore — handles the case where the user landed
        # here via an <a href> click that triggered a full page reload before
        # the auth token was rehydrated into session_state.
        restore_auth()
    if not st.session_state.get("auth_token"):
        st.warning("You must be logged in to view your profile.")
        st.markdown("[Login](?view=login)", unsafe_allow_html=True)
        return

    # NOTE: do NOT inject AUTH_CSS here — it forces .block-container
    # padding-top to 12vh (intended for the centered login/register card)
    # which would push the topbar visibly downward on the profile page.
    inject_css(SETTINGS_CSS)

    email: str = st.session_state.get("auth_email", "")
    first_name: str = st.session_state.get("auth_first_name", "")
    last_name: str = st.session_state.get("auth_last_name", "")
    institution: str = st.session_state.get("auth_institution", "")
    country: str = st.session_state.get("auth_country", "")

    # Fetch institution/country from backend if not yet in session
    if not institution and not country:
        try:
            token = st.session_state.get("auth_token", "")
            profile = get_me(token)
            institution = profile.get("institution") or ""
            country = profile.get("country") or ""
            st.session_state["auth_institution"] = institution
            st.session_state["auth_country"] = country
        except BackendError:
            pass

    if first_name and last_name:
        display_name = f"{first_name} {last_name}"
    elif first_name:
        display_name = first_name
    elif last_name:
        display_name = last_name
    else:
        display_name = email.split("@")[0] if email else ""

    initial = (first_name[0] if first_name else email[0]).upper() if (first_name or email) else "?"

    # Default to "profile" section
    if "_settings_section" not in st.session_state:
        st.session_state["_settings_section"] = "profile"

    active = st.session_state["_settings_section"]

    # ── Hero (full-width gradient, mirrors the logged-in home dashboard) ──
    _hero_subtitle = {
        "profile": "Manage your personal information",
        "security": "Update your password and security settings",
        "feedback": "Send feedback, report a bug, or request a feature",
    }.get(active, "Manage your personal information")
    st.markdown(
        '<div class="settings-hero">'
        f'<h2 class="settings-hero__title">Welcome back, {display_name}</h2>'
        f'<p class="settings-hero__sub">{_hero_subtitle}</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Content shell (sits on top of the gradient → white transition) ───
    st.markdown('<div class="settings-shell">', unsafe_allow_html=True)

    # ── Layout: sidebar + main content ────────────────────────────────────
    col_side, col_main = st.columns([1, 3], gap="large")

    # ── Sidebar ───────────────────────────────────────────────────────────
    with col_side:
        st.markdown(
            '<p class="settings-sidebar__title">Account Settings</p>',
            unsafe_allow_html=True,
        )

        for key, label in _SECTIONS:
            is_active = active == key
            btn_type = "primary" if is_active else "secondary"
            if st.button(
                label,
                key=f"settings_nav_{key}",
                use_container_width=True,
                type=btn_type,
            ):
                st.session_state["_settings_section"] = key
                st.rerun()

        # Back link
        st.markdown("---")
        if st.button(
            "\u2190 Back to Main Page",
            key="settings_back_home",
            use_container_width=True,
        ):
            st.query_params["view"] = "home"
            st.rerun()

    # ── Main content ──────────────────────────────────────────────────────
    with col_main:
        if active == "profile":
            _render_profile(display_name, email, initial, institution, country)
        elif active == "security":
            _render_security()
        elif active == "feedback":
            _render_feedback(email)

    # Close the .settings-shell wrapper opened above the columns.
    st.markdown('</div>', unsafe_allow_html=True)
