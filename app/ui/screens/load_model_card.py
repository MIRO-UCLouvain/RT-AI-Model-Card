"""Module to load a model card from JSON (consistent layout + robust parsing)."""  # noqa: E501

from __future__ import annotations

import json

import streamlit as st

from app.services.state_store import populate_session_state_from_json

INFO_MSG = (
    "Only `.json` files are supported. Please ensure your file is in the "
    "correct format."
)


def load_model_card_page() -> None:
    """Render the page for loading a model card from a JSON file."""
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
    st.header("Load a Model Card")

    st.markdown(
        "<p style='font-size:18px; font-weight:450;'>"
        "Upload a <code>.json</code> model card"
        "</p>",
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload your model card (.json)",
        type=["json"],
        label_visibility="collapsed",
    )

    st.info(INFO_MSG)

    if uploaded_file is not None:
        st.success("File uploaded. Click the button below to load it.")

        if st.button("Load Model Card", use_container_width=True):
            with st.spinner("Parsing and loading model card..."):
                # Robust decoding / parsing
                try:
                    content = uploaded_file.read().decode("utf-8")
                except UnicodeDecodeError:
                    st.error("The file is not valid UTF-8 text.")
                    return

                try:
                    json_data = json.loads(content)
                except json.JSONDecodeError as exc:
                    st.error(
                        f"Invalid JSON: {exc.msg} "
                        f"(line {exc.lineno}, column {exc.colno})",
                    )
                    return

                if not isinstance(json_data, dict):
                    st.error(
                        "Top-level JSON must be an object (e.g., { ... }).",
                    )
                    return

                # Populate state and go to first editable section
                populate_session_state_from_json(json_data)
                from app.ui.screens.sections.card_metadata import (  # noqa: PLC0415
                    card_metadata_render,
                )

                st.session_state.runpage = card_metadata_render
                st.success("Model card loaded successfully!")
                st.rerun()

    if st.button("Return to Main Page", use_container_width=True):
        from app.ui.screens.main import main  # noqa: PLC0415

        st.session_state.runpage = main
        st.rerun()
