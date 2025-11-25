"""Module for the main screen of the RT Model Card application."""

from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st

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
    email: str = st.session_state.get("auth_email", "")
    name = email.split("@")[0] if email else "there"

    st.markdown(f"## Welcome back, **{name}**!")
    st.markdown("What would you like to do?")
    st.markdown("")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("#### Create Model Card")
            st.markdown(
                "Start a new AI model card for your radiotherapy model."
            )
            if st.button(
                "Create Model Card",
                use_container_width=True,
                key="home_create",
            ):
                st.query_params["view"] = "create"
                st.rerun()

        with st.container(border=True):
            st.markdown("#### My Model Cards")
            st.markdown(
                "View and manage the model card you've saved this session."
            )
            if st.button(
                "My Model Cards",
                use_container_width=True,
                key="home_my_cards",
            ):
                st.query_params["view"] = "my_cards"
                st.rerun()

    with col2:
        with st.container(border=True):
            st.markdown("#### Load Model Card")
            st.markdown("Load an existing model card from a JSON file.")
            if st.button(
                "Load Model Card",
                use_container_width=True,
                key="home_load",
            ):
                st.query_params["view"] = "load"
                st.rerun()

        with st.container(border=True):
            st.markdown("#### Published Model Cards")
            st.markdown(
                "Browse approved model cards in the public catalogue."
            )
            if st.button(
                "Published Model Cards",
                use_container_width=True,
                key="home_published",
            ):
                st.query_params["view"] = "published"
                st.rerun()

    st.markdown("---")
    st.link_button(
        "Open an Issue ↗",
        "https://github.com/MIRO-UCLouvain/RT-Model-Card/issues",
    )


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

    # Login/register pages must always be rendered unauthenticated.
    # If stale cookies were restored (race condition: the cookie-clearing JS
    # injected during logout may not have executed before the next full-page
    # reload), clear them now so the UI and browser cookies stay in sync.
    if view in ("login", "register") and (
        st.session_state.get("auth_token") or st.session_state.get("auth_email")
    ):
        clear_auth()

    render_topbar(view, auth_email=st.session_state.get("auth_email"))

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
