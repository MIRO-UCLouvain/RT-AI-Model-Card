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

    st.markdown(_read_about_md())

    st.markdown("---")
    col_back, col_issue = st.columns(2)
    with col_back:
        if st.button("← Back to Main Page", key="about_back_home", use_container_width=True):
            st.query_params["view"] = "home"
            st.rerun()
    with col_issue:
        st.link_button(
            "Open an Issue ↗",
            "https://github.com/MIRO-UCLouvain/RT-Model-Card/issues",
            use_container_width=True,
        )
