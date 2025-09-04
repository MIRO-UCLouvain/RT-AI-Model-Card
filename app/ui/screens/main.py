"""Module for the main application screen."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

ABOUT_TEXT = (
    "Following the **ESTRO Physics Workshop 2023** on "
    "*AI for the Fully Automated Radiotherapy Treatment Chain*, a "
    "working group of 16 experts from 13 institutions developed a "
    "**practical, consensus-driven template** tailored to the unique "
    "requirements of artificial intelligence (AI) models in Radiation "
    "Therapy. The template is designed to enhance transparency, support "
    "informed use, and ensure applicability across both research and "
    "clinical environments. \n\n"
    "This template is **publicly available on Zenodo** as a Microsoft Word "
    "document and as an interactive digital version on this website, making "
    "it easier to standardize reporting and facilitate information entry. "
    "Although aligned with current best practices, it does not replace or "
    "fulfill formal regulatory requirements such as the **EU Medical Device "
    "Regulation or equivalent standards**."
)

def _title_with_logo() -> None:
    """Render the page title with the SVG logo."""
    logo_path = Path("docs/logo/title_logo/title_logo.svg")
    if logo_path.exists():
        col1, col2, col3 = st.columns([1, 3, 1])  # middle col wider
        with col2:
            st.image(str(logo_path), width=500)
    else:
        st.warning(f"Logo not found at: {logo_path}")

# Main page
def main() -> None:
    """Main page for the application."""
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

    _title_with_logo()
    st.markdown(ABOUT_TEXT)
    # Botones de navegación
    if st.button("Create a Model Card", use_container_width=True):
        # Lazy import para evitar ciclos
        from app.ui.screens.task_selector import (  # noqa: PLC0415
            task_selector_page,
        )
        st.session_state.runpage = task_selector_page
        st.rerun()

    if st.button("Load a Model Card", use_container_width=True):
        from app.ui.screens.load_model_card import (  # noqa: PLC0415
            load_model_card_page,
        )
        st.session_state.runpage = load_model_card_page
        st.rerun()

    if st.button("About Model Cards", use_container_width=True):
        from app.ui.screens.about import about_page  # noqa: PLC0415
        st.session_state.runpage = about_page
        st.rerun()

    st.markdown(
        """
        This project is **open-source**.
        You can explore the code, report issues, or contribute on Github.
        Feel free to star the repository if you find it useful!
        \n
        [![GitHub](https://img.shields.io/badge/GitHub-Repository-black?logo=github)](https://github.com/MIRO-UCLouvain/RT-Model-Card)
        """,
        unsafe_allow_html=True,
    )
