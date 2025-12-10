"""About Model Cards page for the Model Cards Writing Tool."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

__all__ = ["model_card_info_render"]

PATH_ERROR_MSG = (
    "File 'about.md' not found.\n\n"
    f"Expected at: {Path.cwd() / 'about.md'}\n"
    "Tip: run Streamlit from the project root and place `about.md` there."
)


@st.cache_data(show_spinner=False)
def _read_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def model_card_info_render() -> None:
    """Render the About Model Cards page."""
    from app.ui.components.sidebar import sidebar_render  # noqa: PLC0415

    sidebar_render()

    md_file = Path("app/content/about.md")
    if not md_file.exists():
        st.error(PATH_ERROR_MSG)
        return

    st.markdown(
        """
        <style>
          .block-container p, .block-container li { text-align: justify; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    try:
        st.markdown(_read_markdown(md_file))
    except UnicodeDecodeError:
        st.error(f"Could not decode '{md_file}' as UTF-8.")
        return

    st.divider()
    _, col, _ = st.columns([1, 2, 1])
    with col:
        if st.button("Start filling up →", use_container_width=True, type="primary"):
            from app.ui.screens.sections.card_metadata import card_metadata_render  # noqa: PLC0415
            st.session_state.runpage = card_metadata_render
            st.rerun()
