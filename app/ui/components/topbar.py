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
) -> None:
    """
    Render the top bar navigation.

    Parameters
    ----------
    active : {"home","create","load","about","published","login","register",
              "my_cards","requests","profile","logout"}
        Which tab to highlight.
    github_url : str | None
        External link for the GitHub repository. If None, a default is used.
    auth_email : str | None
        Email of the logged-in user, or None if not authenticated.
    """
    inject_css(CSS_PATH)

    def cls(name: str) -> str:
        base = "topbar__link"
        return f"{base} topbar__link--active" if name == active else base

    if github_url is None:
        github_url = "https://github.com/MIRO-UCLouvain/RT-Model-Card"

    # --- Auth area (right column) ---
    if auth_email:
        initial = auth_email[0].upper()
        username = auth_email.split("@")[0]
        auth_html = (
            '<div class="topbar__auth">'
            f'<span class="topbar__avatar">{initial}</span>'
            f'<span class="topbar__username">{username}</span>'
            '<a href="?view=logout" target="_self" class="topbar__logout-btn">Logout</a>'
            '</div>'
        )
    else:
        auth_html = (
            '<div class="topbar__auth">'
            f'<a class="{cls("login")}" href="?view=login" target="_self">Login</a>'
            f'<a class="{cls("register")}" href="?view=register" target="_self">Register</a>'
            '</div>'
        )

    st.markdown(
        f"""
        <div class="topbar">
          <div class="topbar__inner">
            <div class="topbar__brand">
              <a class="topbar__home" href="?view=home" target="_self">
                RT AI Model Card Writing Tool
              </a>
            </div>
            <nav class="topbar__nav">
              <a class="{cls('create')}"
                 href="?view=create"
                 target="_self">Create Model Card</a>
              <a class="{cls('published')}"
                 href="?view=published"
                 target="_self">Published Model Cards</a>
            </nav>
            {auth_html}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    """Render the hero section below the top bar."""
    st.markdown(
        """
        <section class="hero hero--long">
          <div class="hero-inner">
            <h1>RadioTherapy AI Model Card — Writing Tool</h1>
            <p class="lead">
              Create AI Model Cards for RadioTherapy with a standardized
              template. It aims to enhance transparency and standardize
              the reporting of AI-based applications in Radiation Therapy.
            </p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
