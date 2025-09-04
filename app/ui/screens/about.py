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
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1100px;
            padding-left: 5rem;
            padding-right: 5rem;
        }
        .block-container p, .block-container li {
            text-align: justify;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <style>
        .block-container p, .block-container li {
            text-align: justify;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Return to Main page"):
        from app.ui.screens.main import main  # noqa: PLC0415
        st.session_state.runpage = main
        st.rerun()
    st.markdown(_read_about_md())

    st.markdown("---")
    if st.button("Return to Main page", use_container_width=True):
        from app.ui.screens.main import main  # noqa: PLC0415
        st.session_state.runpage = main
        st.rerun()
