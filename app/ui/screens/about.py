"""Module to display the extended 'About Model Cards' content."""

from __future__ import annotations

from pathlib import Path

import streamlit as st


def _read_about_md() -> str:
    md_path = Path("app/content/about.md")
    if not md_path.exists():
        return (
            f"**about.md not found.** Expected at `{md_path}`.\n\n"
            "Please make sure the file exists."
        )
    return md_path.read_text(encoding="utf-8")


def about_page() -> None:
    """Display the extended 'About Model Cards' content."""
    st.markdown(_read_about_md())

    st.markdown("---")
    _, col_back, _ = st.columns([1, 2, 1])
    with col_back:
        if st.button("← Back to Main Page", key="about_back_home", use_container_width=True):
            st.query_params["view"] = "home"
            st.rerun()
