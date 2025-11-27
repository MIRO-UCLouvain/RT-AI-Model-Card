"""Module for the main screen of the RT Model Card application."""

from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st

from app.client.model_cards import BackendError, get_me
from app.ui.components.topbar import render_hero, render_topbar
from app.ui.screens.about import about_page
from app.ui.screens.load_model_card import load_model_card_page
from app.ui.screens.login import login_page
from app.ui.screens.my_cards import my_cards_page
from app.ui.screens.profile import profile_page
from app.ui.screens.published_cards import published_cards_page
from app.ui.screens.register import register_page
from app.ui.screens.task_selector import task_selector_page
from app.ui.utils.auth import clear_auth, restore_auth, restore_card_state
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
    else:
        display_name = email.split("@")[0] if email else "there"

    # Welcome header — flat string, no indentation (avoids markdown code-block issue)
    st.markdown(
        '<div style="padding:1.5rem 0 0.5rem;">'
        f'<h2 style="margin:0 0 0.25rem;color:var(--ink);font-size:1.6rem;font-weight:700;">'
        f'Welcome, <span style="color:var(--brand-600)">{display_name}</span>'
        '</h2>'
        '<p style="margin:0;color:var(--muted);font-size:0.9rem;">Select an action to get started.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── 2×2 dashboard grid ────────────────────────────────────────────────
    col1, col2 = st.columns(2, gap="medium")

    with col1:
        with st.container(border=True):
            st.markdown(
                '<p class="dash-card__title">Create Model Card</p>'
                '<p class="dash-card__desc">Build a new AI model card using the standardised RT template.</p>',
                unsafe_allow_html=True,
            )
            if st.button("Create Model Card", use_container_width=True, key="home_create"):
                st.query_params["view"] = "create"
                st.rerun()

        with st.container(border=True):
            st.markdown(
                '<p class="dash-card__title">My Model Cards</p>'
                '<p class="dash-card__desc">View and submit cards you have saved in this session.</p>',
                unsafe_allow_html=True,
            )
            if st.button("My Model Cards", use_container_width=True, key="home_my_cards"):
                st.query_params["view"] = "my_cards"
                st.rerun()

    with col2:
        with st.container(border=True):
            st.markdown(
                '<p class="dash-card__title">Load Model Card</p>'
                '<p class="dash-card__desc">Resume editing by uploading an existing card from a JSON file.</p>',
                unsafe_allow_html=True,
            )
            if st.button("Load Model Card", use_container_width=True, key="home_load"):
                st.query_params["view"] = "load"
                st.rerun()

        with st.container(border=True):
            st.markdown(
                '<p class="dash-card__title">Published Model Cards</p>'
                '<p class="dash-card__desc">Browse cards that have been reviewed and approved for publication.</p>',
                unsafe_allow_html=True,
            )
            if st.button("Published Model Cards", use_container_width=True, key="home_published"):
                st.query_params["view"] = "published"
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

    # If a token was restored but the name cookies were empty (e.g. the
    # components.html JS that sets cookies ran after the next page load),
    # fetch the profile once and backfill session state so the display name
    # is always First + Last, never the email prefix.
    if (
        st.session_state.get("auth_token")
        and not st.session_state.get("auth_first_name")
        and not st.session_state.get("auth_last_name")
    ):
        try:
            _profile = get_me(st.session_state.auth_token)
            st.session_state.auth_first_name = _profile.get("first_name") or ""
            st.session_state.auth_last_name = _profile.get("last_name") or ""
        except BackendError:
            pass

    # Login/register pages must always be rendered unauthenticated.
    # If stale cookies were restored (race condition: the cookie-clearing JS
    # injected during logout may not have executed before the next full-page
    # reload), clear session state inline — do NOT call clear_auth() here
    # because its components.html injection inside the render path can cause
    # visual artifacts (form appearing twice).
    if view in ("login", "register") and (
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
    )

    if view == "create":
        task_selector_page()
        return

    if view == "load":
        load_model_card_page()
        return

    if view == "about":
        about_page()
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

    if view in ("my_cards", "requests"):
        my_cards_page()
        return

    if view == "profile":
        profile_page()
        return

    # Home — different content depending on auth state
    if st.session_state.get("auth_token"):
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
