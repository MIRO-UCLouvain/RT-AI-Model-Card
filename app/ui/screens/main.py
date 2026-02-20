"""Module for the main screen of the RT Model Card application."""

from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st

from app.client.model_cards import BackendError, get_me
from app.ui.components.topbar import render_hero, render_topbar
from app.ui.screens.about import about_page
from app.ui.screens.feedback import feedback_page
from app.ui.screens.forgot_password import forgot_password_page
from app.ui.screens.load_model_card import load_model_card_page
from app.ui.screens.login import login_page
from app.ui.screens.admin import admin_page
from app.ui.screens.my_cards import my_cards_page
from app.ui.screens.profile import profile_page
from app.ui.screens.published_cards import published_cards_page
from app.ui.screens.register import register_page
from app.ui.screens.reset_password import reset_password_page
from app.ui.screens.task_selector import task_selector_page
from app.services.state_store import clear_form_state
from app.ui.utils.auth import clear_auth, clear_card_state, restore_auth, restore_card_state
from app.ui.utils.css import inject_css

CSS_PATH = Path(__file__).resolve().parent.parent / "static" / "global.css"

logger = logging.getLogger(__name__)

ABOUT_TEXT = (
    "Following the **ESTRO Physics Workshop 2023** on "
    "*AI for the Fully Automated Radiotherapy Treatment Chain*, "
    "a working group of 16 experts from 13 institutions developed a "
    "**practical, consensus-driven template** tailored to the unique "
    "requirements of artificial intelligence (AI) models in Radiation "
    "Therapy. The template is designed to enhance transparency, support "
    "informed use, and ensure applicability across both research and "
    "clinical environments.\n\n"
    "This template is **publicly available on Zenodo** as a Microsoft "
    "Word document and as an interactive digital version on this website, "
    "making it easier to standardize reporting and facilitate information "
    "entry. Although aligned with current best practices, it does not "
    "replace or fulfill formal regulatory requirements such as the "
    "**EU Medical Device Regulation or equivalent standards**."
)


def _title_with_logo() -> None:
    """Render the logo centered below the hero."""
    logo_path = Path("docs/logo/title_logo/title_logo.svg")
    if logo_path.exists():
        cols = st.columns([1, 3, 1])
        with cols[1]:
            st.image(str(logo_path), width=700)
    else:
        st.warning(f"Logo not found at: {logo_path}")


def _get_view() -> str:
    """Return the target view from query params, defaulting to 'home'."""
    try:
        qp = getattr(st, "query_params", None)
        if qp is None:
            return "home"

        value = qp.get("view")
        if isinstance(value, list):
            value = value[0] if value else None

    except Exception:  # pragma: no cover
        logger.exception("Failed to read 'view' from st.query_params")
        return "home"
    else:
        if value:
            return str(value).lower()
        return "home"


def _render_github_repo(repo_url: str) -> None:
    """Render only clickable shields/badges linking to the repo."""
    owner_repo = repo_url.split("github.com/")[-1]

    st.markdown(
        (
            '<div class="home-actions">'
            '<p class="home-actions__copy">'
            'This project is <strong>open-source</strong>. Explore the code, '
            'report issues, or contribute on GitHub.'
            '</p>'
            '<div class="home-actions__badges">'
            f'<a href="{repo_url}" target="_blank" rel="noopener noreferrer" '
            'aria-label="GitHub repository">'
            '<img alt="GitHub" '
            'src="https://img.shields.io/badge/GitHub-Repository-181717'
            '?logo=github&logoColor=white" />'
            '</a> '
            f'<a href="{repo_url}/stargazers" '
            'target="_blank" rel="noopener noreferrer" '
            'aria-label="GitHub stars">'
            f'<img alt="GitHub stars" '
            f'src="https://img.shields.io/github/stars/{owner_repo}'
            '?style=social" />'
            '</a>'
            '</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


def _render_logged_in_home() -> None:
    """Render the action dashboard shown to authenticated users."""
    first_name: str = st.session_state.get("auth_first_name") or ""
    last_name: str = st.session_state.get("auth_last_name") or ""
    email: str = st.session_state.get("auth_email", "")

    if first_name and last_name:
        display_name = f"{first_name} {last_name}"
    elif first_name:
        display_name = first_name
    elif last_name:
        display_name = last_name
    else:
        display_name = email.split("@")[0] if email else "there"

    # ── Hero banner ─────────────────────────────────────────────────────────
    st.markdown(
        '<div class="dash-hero">'
        '<h2 class="dash-hero__title">'
        f'Welcome back, {display_name}'
        '</h2>'
        '<p class="dash-hero__sub">'
        'Create and manage AI Model Cards for Radiation Therapy'
        '</p>'
        '</div>',
        unsafe_allow_html=True,
    )


    # ── Primary CTA — Create Model Card ──────────────────────────────────
    with st.container(border=True):
        st.markdown(
            '<div class="dash-cta">'
            '<div class="dash-cta__icon">'
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>'
            '</svg>'
            '</div>'
            '<div class="dash-cta__text">'
            '<p class="dash-cta__title">Create a new Model Card</p>'
            '<p class="dash-cta__desc">'
            'Build a comprehensive AI model card using the standardised AID-RT template.'
            '</p>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button("Create Model Card", use_container_width=True, key="home_create"):
            clear_form_state()
            clear_card_state()
            st.query_params["view"] = "create"
            st.rerun()

    # ── Two cards: Load + Published ──────────────────────────────────────
    c1, c2 = st.columns(2, gap="medium")

    with c1:
        with st.container(border=True):
            st.markdown(
                '<div class="dash-card__icon dash-card__icon--load">'
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
                'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
                '<polyline points="7 10 12 15 17 10"/>'
                '<line x1="12" y1="15" x2="12" y2="3"/>'
                '</svg></div>'
                '<p class="dash-card__title">Load Model Card</p>'
                '<p class="dash-card__desc">'
                'Upload a previously exported JSON file to resume editing.'
                '</p>',
                unsafe_allow_html=True,
            )
            if st.button("Load from file", use_container_width=True, key="home_load"):
                st.query_params["view"] = "load"
                st.rerun()

    with c2:
        with st.container(border=True):
            st.markdown(
                '<div class="dash-card__icon dash-card__icon--published">'
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
                'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                '<circle cx="12" cy="12" r="10"/>'
                '<line x1="2" y1="12" x2="22" y2="12"/>'
                '<path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>'
                '</svg></div>'
                '<p class="dash-card__title">Published Cards</p>'
                '<p class="dash-card__desc">'
                'Browse the public catalogue of approved model cards.'
                '</p>',
                unsafe_allow_html=True,
            )
            if st.button("Browse catalogue", use_container_width=True, key="home_published"):
                st.query_params["view"] = "published"
                st.rerun()

    # ── My Model Cards actions — 3 mini cards ──────────────────────────────
    b1, b2, b3 = st.columns(3, gap="medium")

    with b1:
        with st.container(border=True):
            st.markdown(
                '<div class="dash-mini">'
                '<div class="dash-mini__icon">'
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
                'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
                '<polyline points="14 2 14 8 20 8"/>'
                '<line x1="16" y1="13" x2="8" y2="13"/>'
                '<line x1="16" y1="17" x2="8" y2="17"/>'
                '</svg></div>'
                '<div class="dash-mini__text">'
                '<p class="dash-mini__title">View My Cards</p>'
                '<p class="dash-mini__desc">Browse and manage your saved model cards</p>'
                '</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            if st.button("Open", use_container_width=True, key="home_my_cards"):
                st.session_state["_my_cards_section"] = "cards"
                st.query_params["view"] = "my_cards"
                st.rerun()

    with b2:
        with st.container(border=True):
            st.markdown(
                '<div class="dash-mini">'
                '<div class="dash-mini__icon">'
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
                'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                '<polyline points="16 18 22 12 16 6"/>'
                '<polyline points="8 6 2 12 8 18"/>'
                '</svg></div>'
                '<div class="dash-mini__text">'
                '<p class="dash-mini__title">Compare Versions</p>'
                '<p class="dash-mini__desc">Side-by-side diff between card versions</p>'
                '</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            if st.button("Open", use_container_width=True, key="home_compare"):
                st.session_state["_my_cards_section"] = "compare"
                st.query_params["view"] = "my_cards"
                st.rerun()

    with b3:
        with st.container(border=True):
            st.markdown(
                '<div class="dash-mini">'
                '<div class="dash-mini__icon">'
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
                'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                '<line x1="22" y1="2" x2="11" y2="13"/>'
                '<polygon points="22 2 15 22 11 13 2 9 22 2"/>'
                '</svg></div>'
                '<div class="dash-mini__text">'
                '<p class="dash-mini__title">Request Publication</p>'
                '<p class="dash-mini__desc">Submit a version for admin review</p>'
                '</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            if st.button("Open", use_container_width=True, key="home_publish"):
                st.session_state["_my_cards_section"] = "requests"
                st.query_params["view"] = "my_cards"
                st.rerun()


def main() -> None:
    """Entrypoint for the main screen and simple router."""
    inject_css(CSS_PATH)

    view = _get_view()

    # Handle logout BEFORE restore_auth() so that clicking the topbar logout
    # link (which causes a full page reload) doesn't re-read the auth cookies
    # before we get a chance to clear them.
    if view == "logout":
        clear_auth()
        st.query_params["view"] = "home"
        st.rerun()
        return

    # Restore auth and card state from browser cookies after a page reload
    restore_auth()
    restore_card_state()

    # Fetch the user profile once per session start whenever the token is
    # present but is_admin (or the display name) is not yet in session state.
    # This ensures admins see the Admin Panel link without a second login.
    if st.session_state.get("auth_token") and "auth_is_admin" not in st.session_state:
        try:
            _profile = get_me(st.session_state.auth_token)
            st.session_state.auth_first_name = _profile.get("first_name") or ""
            st.session_state.auth_last_name = _profile.get("last_name") or ""
            st.session_state.auth_is_admin = bool(_profile.get("is_admin", False))
        except BackendError:
            st.session_state.auth_is_admin = False

    # Login/register/password-reset pages must always be rendered unauthenticated.
    # If stale cookies were restored (race condition: the cookie-clearing JS
    # injected during logout may not have executed before the next full-page
    # reload), clear session state inline — do NOT call clear_auth() here
    # because its components.html injection inside the render path can cause
    # visual artifacts (form appearing twice).
    if view in ("login", "register", "forgot_password", "reset_password") and (
        st.session_state.get("auth_token") or st.session_state.get("auth_email")
    ):
        st.session_state.auth_token = None
        st.session_state.auth_email = None
        st.session_state.auth_first_name = None
        st.session_state.auth_last_name = None
        st.session_state["_auth_logged_out"] = True

    render_topbar(
        view,
        auth_email=st.session_state.get("auth_email"),
        auth_first_name=st.session_state.get("auth_first_name"),
        auth_last_name=st.session_state.get("auth_last_name"),
        auth_is_admin=bool(st.session_state.get("auth_is_admin", False)),
    )

    is_admin = bool(st.session_state.get("auth_is_admin", False))
    is_logged_in = bool(st.session_state.get("auth_token"))

    # ── Admin guard: redirect admins away from regular-user views ────────
    _user_only_views = {"create", "load", "my_cards", "requests"}
    if is_admin and is_logged_in and view in _user_only_views:
        st.query_params["view"] = "admin"
        st.rerun()
        return

    if view == "create":
        task_selector_page()
        return

    if view == "load":
        load_model_card_page()
        return

    if view == "about":
        about_page()
        return

    if view == "contact":
        if is_logged_in:
            st.session_state["_settings_section"] = "feedback"
            st.query_params["view"] = "profile"
            st.rerun()
        else:
            feedback_page()
        return

    if view == "published":
        published_cards_page()
        return

    if view == "login":
        login_page()
        return

    if view == "register":
        register_page()
        return

    if view == "forgot_password":
        forgot_password_page()
        return

    if view == "reset_password":
        reset_password_page()
        return

    if view in ("my_cards", "requests"):
        my_cards_page()
        return

    if view == "profile":
        profile_page()
        return

    if view == "admin":
        admin_page()
        return

    # Home — admins go straight to the admin panel
    if is_logged_in and is_admin:
        admin_page()
        return

    if is_logged_in:
        _render_logged_in_home()
    else:
        render_hero()
        st.markdown('<div class="home-copy">', unsafe_allow_html=True)
        _title_with_logo()
        st.markdown(ABOUT_TEXT)
        _render_github_repo(
            repo_url="https://github.com/MIRO-UCLouvain/RT-Model-Card",
        )
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.link_button(
            "Open an Issue ↗",
            "https://github.com/MIRO-UCLouvain/RT-Model-Card/issues",
        )


if __name__ == "__main__":
    main()
