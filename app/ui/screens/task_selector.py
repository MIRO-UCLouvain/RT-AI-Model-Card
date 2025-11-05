"""Module to select the task for the Model Card (with stable centered layout)."""  # noqa: E501

from __future__ import annotations

import streamlit as st


def task_selector_page() -> None:
    """Render the task selector page."""
    st.markdown(
        """
        <style>
        /* Contenedor central de todo el bloque */
        .radio-center {
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 100%;
            gap: 2rem; /* Espacio uniforme entre título, caja y botón */
        }

        /* Caja de opciones centrada */
        div[role="radiogroup"] {
            background-color: #f9f9f9;
            padding: 2rem 3rem;   /* Más grande */
            border-radius: 20px;
            border: 2px solid #0553D1;  /* Borde azul */
            display: inline-block;
            text-align: left;
            margin: auto;
            width: 100%;
            max-width: 600px;
        }

        /* Texto de las opciones */
        label[data-baseweb="radio"] > div:first-child {
            font-size: 22px !important;
            padding: 6px 0;
        }

        /* Opción seleccionada */
        div[role="radiogroup"] input:checked + div {
            color: #0553D1 !important;
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
        st.markdown("<br>", unsafe_allow_html=True)
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

    st.markdown("</div>", unsafe_allow_html=True)
