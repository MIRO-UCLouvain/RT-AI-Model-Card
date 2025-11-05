"""Module for the main screen of the RT Model Card application."""

from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st

from app.ui.components.topbar import render_hero, render_topbar
from app.ui.screens.about import about_page
from app.ui.screens.load_model_card import load_model_card_page
from app.ui.screens.task_selector import task_selector_page
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

def main() -> None:
    """Entrypoint for the main screen and simple router."""
    inject_css(CSS_PATH)

    view = _get_view()
    render_topbar(view)

    if view == "create":
        task_selector_page()
        return

    if view == "load":
        load_model_card_page()
        return

    if view == "about":
        about_page()
        return

    # Home
    render_hero()
    # Use one shared, larger text style for ABOUT + repo
    st.markdown('<div class="home-copy">', unsafe_allow_html=True)
    _title_with_logo()
    st.markdown(ABOUT_TEXT)
    _render_github_repo(
        repo_url="https://github.com/MIRO-UCLouvain/RT-Model-Card",
    )
    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
