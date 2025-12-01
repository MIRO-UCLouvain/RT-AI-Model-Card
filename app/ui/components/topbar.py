"""Top bar + hero (SPA with ?view=... in the same window)."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.ui.utils.css import inject_css

CSS_PATH = Path(__file__).resolve().parent.parent / "static" / "topbar.css"


def render_topbar(
    active: str,
    github_url: str | None = None,
    auth_email: str | None = None,
    auth_first_name: str | None = None,
    auth_last_name: str | None = None,
) -> None:
    """
    Render the top bar navigation.

    Parameters
    ----------
    active : str
        Which view is currently active (used to highlight the active link).
    github_url : str | None
        External link for the GitHub repository.
    auth_email : str | None
        Email of the logged-in user, or None if not authenticated.
    auth_first_name : str | None
        First name of the logged-in user.
    auth_last_name : str | None
        Last name of the logged-in user.
    """
    inject_css(CSS_PATH)

    def cls(name: str) -> str:
        base = "topbar__link"
        return f"{base} topbar__link--active" if name == active else base

    if github_url is None:
        github_url = "https://github.com/MIRO-UCLouvain/RT-Model-Card"

    if auth_email:
        # Authenticated: no discovery nav; show user profile dropdown.
        if auth_first_name and auth_last_name:
            display_name = f"{auth_first_name} {auth_last_name}"
        elif auth_first_name:
            display_name = auth_first_name
        elif auth_last_name:
            display_name = auth_last_name
        else:
            display_name = auth_email.split("@")[0]
        initial = (auth_first_name[0] if auth_first_name else auth_email[0]).upper()
        # Flat string — no indentation so Python-Markdown never treats it as a code block.
        nav_html = ""
        auth_html = (
            '<div class="topbar__auth">'
            '<div class="topbar__profile" tabindex="0">'
            '<div class="topbar__profile-trigger">'
            f'<span class="topbar__avatar">{initial}</span>'
            f'<span class="topbar__username">{display_name}</span>'
            '<span class="topbar__chevron">&#9660;</span>'
            "</div>"
            '<div class="topbar__dropdown">'
            '<div class="topbar__dropdown-header">'
            f'<div class="topbar__dropdown-name">{display_name}</div>'
            f'<div class="topbar__dropdown-email">{auth_email}</div>'
            "</div>"
            '<div class="topbar__dropdown-divider"></div>'
            '<a href="?view=logout" target="_self" class="topbar__dropdown-logout">Logout</a>'
            "</div>"
            "</div>"
            "</div>"
        )
    else:
        # Unauthenticated: show entry-level nav + login/register.
        nav_html = (
            f'<a class="{cls("create")}" href="?view=create" target="_self">Create Model Card</a>'
            f'<a class="{cls("published")}" href="?view=published" target="_self">Published Model Cards</a>'
        )
        auth_html = (
            '<div class="topbar__auth">'
            f'<a class="{cls("login")}" href="?view=login" target="_self">Login</a>'
            f'<a class="{cls("register")}" href="?view=register" target="_self">Register</a>'
            "</div>"
        )

    # Build as a single flat string — critical: no leading whitespace on any line,
    # otherwise Python-Markdown interprets indented lines as code blocks.
    html = (
        '<div class="topbar">'
        '<div class="topbar__inner">'
        '<div class="topbar__brand">'
        '<a class="topbar__home" href="?view=home" target="_self">RT AI Model Card Writing Tool</a>'
        "</div>"
        f'<nav class="topbar__nav">{nav_html}</nav>'
        + auth_html
        + "</div>"
        "</div>"
    )

    st.markdown(html, unsafe_allow_html=True)


def render_hero() -> None:
    """Render the hero section below the top bar."""
    st.markdown(
        '<section class="hero hero--long">'
        '<div class="hero-inner">'
        "<h1>RadioTherapy AI Model Card — Writing Tool</h1>"
        '<p class="lead">'
        "Create AI Model Cards for RadioTherapy with a standardized "
        "template. It aims to enhance transparency and standardize "
        "the reporting of AI-based applications in Radiation Therapy."
        "</p>"
        "</div>"
        "</section>",
        unsafe_allow_html=True,
    )
