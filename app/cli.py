"""Launcher for the Model Cards Writing Tool."""
import streamlit as st

from app.ui.screens.main import main

# Views where a non-main runpage is valid (the model-card form sections live
# under ?view=create; the URL stays "create" while the user moves between
# sections via the sidebar).
_SECTION_VIEWS: frozenset[str] = frozenset({"create"})

if __name__ == "__main__":
    view = (st.query_params.get("view") or "home").lower()

    # For every view outside the form-editing flow always route through
    # main().  This prevents stale section runpages from showing the wrong
    # page (and hiding the top bar) when the user navigates away.
    if "runpage" not in st.session_state or view not in _SECTION_VIEWS:
        st.session_state.runpage = main

    st.session_state.runpage()
