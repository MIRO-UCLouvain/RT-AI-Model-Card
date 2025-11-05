"""Module for CSS utilities."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import streamlit as st


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")

@lru_cache(maxsize=16)
def load_css_text(path: str | Path) -> str:
    """
    Load CSS text (cached).

    :param path: Path to the CSS file.
    :type path: str | Path
    :return: CSS text.
    :rtype: str
    """
    p = Path(path)
    return _read_text(p)

def inject_css(path: str | Path) -> None:
    """
    Read CSS from file and inject into the page.

    :param path: Path to the CSS file.
    :type path: str | Path
    """
    try:
        css = load_css_text(str(path))
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except OSError as e:
        st.error(f"Failed to load CSS: {e}")

def inject_many(paths: list[str | Path]) -> None:
    """
    Inject multiple CSS files in order.

    :param paths: List of paths to CSS files.
    :type paths: list[str  |  Path]
    """
    for p in paths:
        inject_css(p)
