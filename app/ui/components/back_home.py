"""Back-to-main-page button guarded by an unsaved-changes confirmation."""

from __future__ import annotations

import streamlit as st

from app.core.model_card.constants import SCHEMA
from app.services.serialization import parse_into_json
from app.services.state_store import clear_form_state, has_form_data

__all__ = ["render_back_to_home"]

BACK_LABEL = "← Back to main page"
UNSAVED_WARNING = (
    "You have unsaved changes. If you leave, your model card data will be "
    "lost unless you download it first."
)

# The dialog must be re-created on every rerun while it is open: a click on
# one of its own widgets reruns the script, and a dialog that isn't rendered
# again simply disappears, swallowing the click.
_DIALOG_OPEN = "_confirm_leave_open"


def _close_dialog() -> None:
    st.session_state.pop(_DIALOG_OPEN, None)


def _go_home() -> None:
    """Discard the current card and return to the landing page."""
    _close_dialog()
    clear_form_state()
    st.query_params["view"] = "home"
    st.rerun()


@st.dialog("Leave without saving?")
def _confirm_leave_dialog() -> None:
    """Ask the user to download, leave anyway, or stay."""
    st.warning(UNSAVED_WARNING)

    st.download_button(
        "Download model card",
        data=parse_into_json(SCHEMA),
        file_name="model_card.json",
        mime="application/json",
        use_container_width=True,
        key="dlg_download_card",
    )

    col_leave, col_stay = st.columns(2)
    with col_leave:
        if st.button(
            "Go to main page",
            use_container_width=True,
            key="dlg_go_home",
        ):
            _go_home()
    with col_stay:
        if st.button("Stay", use_container_width=True, key="dlg_stay"):
            _close_dialog()
            st.rerun()


def render_back_to_home(key: str) -> None:
    """Render the back button, confirming first when there is data to lose.

    :param key: Unique Streamlit key, so several screens can render it.
    :type key: str
    """
    if st.button(BACK_LABEL, key=key, use_container_width=True):
        if has_form_data():
            st.session_state[_DIALOG_OPEN] = True
        else:
            _go_home()

    if st.session_state.get(_DIALOG_OPEN):
        _confirm_leave_dialog()
