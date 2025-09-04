"""Module to select the task for the Model Card (with stable centered layout)."""  # noqa: E501
from __future__ import annotations

import streamlit as st


def task_selector_page() -> None:
    """Render the task selector page."""
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
    # Inject the page CSS every render so layout is stable on reload
    st.markdown(
        """
        <style>
        /* Contenedor central de todo el bloque */
        .radio-center {
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 100%;
        }
        /* Caja de opciones centrada */
        div[role="radiogroup"] {
            background-color: #f9f9f9;
            padding: 1rem 2rem;
            border-radius: 20px;
            border: 1px solid #ddd;
            display: inline-block;
            text-align: left;
            margin: auto;
        }
        label[data-baseweb="radio"] > div:first-child {
            font-size: 20px !important;
            padding: 4px 0;
        }
        div[role="radiogroup"] input:checked + div {
            color: #1E88E5 !important;
            font-weight: bold;
        }
        label[data-baseweb="radio"] {
            margin-bottom: 6px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Always render the wrapper so width/centering don't change after reload
    st.markdown("<div class='radio-center'>", unsafe_allow_html=True)
    st.markdown(
        "<h2 style='text-align: center;'>"
        "Select the task for your Model Card</h2>",
        unsafe_allow_html=True,
    )

    if "task" not in st.session_state:
        left, center, right = st.columns([1, 1, 1])
        with center:
            selected_task = st.radio(
                ".",
                [
                    "Image-to-Image translation",
                    "Segmentation",
                    "Dose prediction",
                    "Other",
                ],
                key="task_temp",
                label_visibility="hidden",
            )

        if st.button("Continue", use_container_width=True):
            st.session_state["task"] = selected_task
            # Lazy import to avoid circular import
            from app.ui.screens.sections.model_card_info import (  # noqa: PLC0415
                model_card_info_render,
            )

            st.session_state.runpage = model_card_info_render
            st.rerun()
    else:
        st.success(f"Task already selected: **{st.session_state['task']}**")

    if st.button("Return to Main Page", use_container_width=True):
        from app.ui.screens.main import main  # noqa: PLC0415
        st.session_state.runpage = main
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
