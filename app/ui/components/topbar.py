"""Top bar + hero (SPA with ?view=... in the same window)."""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

from app.ui.utils.css import inject_css

CSS_PATH = Path(__file__).resolve().parent.parent / "static" / "topbar.css"

def _load_github_icon_b64() -> str | None:
    """Return base64 of the GitHub icon if found, else None."""
    candidates = [
        Path("docs/logo/github_logo/github_logo.png"),
        Path(__file__).resolve().parents[3]
        / "docs" / "logo" / "github_logo" / "github_logo.png",
    ]
    for p in candidates:
        try:
            if p.exists():
                return base64.b64encode(p.read_bytes()).decode("ascii")
        except OSError:
            continue
    return None


def render_topbar(active: str, github_url: str | None = None) -> None:
    """
    Render the top bar navigation.

    Parameters
    ----------
    active : {"home","create","load","about"}
        Which tab to highlight.
    github_url : str | None
        External link for the GitHub icon. If None, a default is used.
    """
    inject_css(CSS_PATH)

    def cls(name: str) -> str:
        base = "topbar__link"
        return f"{base} topbar__link--active" if name == active else base

    if github_url is None:
        github_url = "https://github.com/MIRO-UCLouvain/RT-Model-Card"

    # --- GitHub icon (embedded base64 so it always shows) ---
    icon_b64 = _load_github_icon_b64()
    if icon_b64:
        icon_html = (
            f'<a class="topbar__iconlink" href="{github_url}" '
            f'target="_self" aria-label="GitHub">'
            f'<img class="topbar__icon" '
            f'src="data:image/png;base64,{icon_b64}" alt="GitHub"/></a>'
        )
    else:
        # Fallback text link if file is missing
        icon_html = (
            f'<a class="{cls("github")}" href="{github_url}" '
            f'target="_self" aria-label="GitHub">GitHub</a>'
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
                 target="_self">Create</a>
              <a class="{cls('load')}"
                 href="?view=load"
                 target="_self">Load</a>
              <a class="{cls('about')}"
                 href="?view=about"
                 target="_self">About</a>
              {icon_html}
            </nav>
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
