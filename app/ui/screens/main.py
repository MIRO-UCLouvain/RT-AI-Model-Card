"""Module for the main screen of the RT Model Card application."""

from __future__ import annotations

import base64
import logging
from functools import lru_cache
from pathlib import Path

import markdown
import streamlit as st

from app.ui.components.topbar import render_hero, render_topbar
from app.ui.screens.about import about_page
from app.ui.screens.load_model_card import load_model_card_page
from app.ui.screens.task_selector import task_selector_page
from app.ui.utils.css import inject_css

CSS_PATH = Path(__file__).resolve().parent.parent / "static" / "global.css"
LOGO_PATH = (
    Path(__file__).resolve().parents[3]
    / "docs" / "logo" / "title_logo" / "title_logo.svg"
)

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


@lru_cache(maxsize=1)
def _logo_data_uri() -> str:
    """Return the title logo as an inline data URI."""
    b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


def _render_home_intro() -> None:
    """Render the logo and the intro copy as one two-column block.

    Everything goes in a single markdown call: Streamlit isolates each block,
    so a wrapper opened in one call would close empty and never lay out (or
    style) the elements that follow it.
    """
    if LOGO_PATH.exists():
        logo = (
            '<div class="home-logo">'
            f'<img src="{_logo_data_uri()}" '
            'alt="RadioTherapy AI Model Card writing tool" />'
            "</div>"
        )
    else:
        logo = ""
        st.warning(f"Logo not found at: {LOGO_PATH}")

    st.markdown(
        '<div class="home-intro">'
        f"{logo}"
        f'<div class="home-copy">{markdown.markdown(ABOUT_TEXT)}</div>'
        "</div>",
        unsafe_allow_html=True,
    )


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
    owner_repo = repo_url.rsplit("github.com/", maxsplit=1)[-1]

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
    _render_home_intro()
    _render_github_repo(
        repo_url="https://github.com/MIRO-UCLouvain/RT-Model-Card",
    )


if __name__ == "__main__":
    main()
