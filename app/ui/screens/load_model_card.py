"""Module to load a model card from JSON (consistent layout + robust parsing)."""  # noqa: E501

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import streamlit as st

from app.services.state_store import (
    clear_form_state,
    populate_session_state_from_json,
)
from app.ui.components.back_home import render_back_to_home

if TYPE_CHECKING:
    from streamlit.runtime.uploaded_file_manager import UploadedFile

INFO_MSG = (
    "Only `.json` files are supported. Please ensure your file is in the "
    "correct format."
)
CSS_PATH = (Path(__file__).resolve().parent.parent / "static" / "global.css")

def _read_card(uploaded_file: UploadedFile) -> dict[str, Any] | None:
    """Decode and parse the upload, reporting problems to the user.

    :return: The parsed model card, or None when the file can't be used.
    """
    try:
        content = uploaded_file.read().decode("utf-8")
    except UnicodeDecodeError:
        st.error("The file is not valid UTF-8 text.")
        return None

    try:
        json_data = json.loads(content)
    except json.JSONDecodeError as exc:
        st.error(
            f"Invalid JSON: {exc.msg} (line {exc.lineno}, column {exc.colno})",
        )
        return None

    if not isinstance(json_data, dict):
        st.error("Top-level JSON must be an object (e.g., { ... }).")
        return None

    return json_data


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
                loaded = _read_card(uploaded_file)
            if loaded is not None:
                # Start from a clean form so nothing from a previously
                # opened card survives into the one being loaded.
                clear_form_state()
                populate_session_state_from_json(loaded)

                from app.ui.screens.sections.card_metadata import (  # noqa: PLC0415
                    card_metadata_render,
                )

                st.session_state.runpage = card_metadata_render
                st.success("Model card loaded successfully!")
                st.rerun()

    st.markdown("---")
    _, col_back, _ = st.columns([2, 1, 2])
    with col_back:
        render_back_to_home(key="load_back_home")
