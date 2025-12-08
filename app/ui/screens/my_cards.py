"""My Model Cards screen — session card management and publish requests.

Handles both ?view=my_cards and ?view=requests (alias).

Note: the backend has no "list cards for this user" endpoint, so this screen
only shows cards saved in the current browser session (tracked via
saved_card_id in session_state). Refreshing the page resets this view.
"""

from __future__ import annotations

import streamlit as st

from app.client.model_cards import BackendError, get_versions, request_publication
from app.services.state_store import populate_session_state_from_json

_STATUS_DISPLAY: dict[str, tuple[str, str]] = {
    "draft":    ("Draft — not submitted", "info"),
    "pending":  ("Pending review",        "warning"),
    "approved": ("Published ✓",           "success"),
    "rejected": ("Rejected",              "error"),
}


def my_cards_page() -> None:
    """Render the My Model Cards screen with My Cards and Requests tabs."""
    if not st.session_state.get("auth_token"):
        st.warning("You must be logged in to view your model cards.")
        st.markdown(
            "[Login](?view=login)  ·  [Register](?view=register)",
            unsafe_allow_html=True,
        )
        return

    st.header("My Model Cards")

    card_id: int | None = st.session_state.get("saved_card_id")
    version: int | None = st.session_state.get("saved_version")
    slug: str = st.session_state.get("saved_slug", "") or ""
    status: str = st.session_state.get("saved_publication_status", "draft")
    token: str | None = st.session_state.get("auth_token")

    tab_cards, tab_requests = st.tabs(["My Cards", "Requests to Publish"])

    with tab_cards:
        if card_id is None:
            st.info("No model card saved in this session yet.")
            st.markdown(
                "Start by [creating a model card](?view=create) "
                "and saving it from the sidebar.",
                unsafe_allow_html=True,
            )
        else:
            with st.container(border=True):
                col_info, col_btn = st.columns([4, 1])
                with col_info:
                    st.markdown(f"**{slug or 'Unnamed card'}**")
                    st.caption(
                        f"ID: {card_id} · Version: {version} · "
                        f"Status: {status.title()}"
                    )
                with col_btn:
                    if st.button(
                        "Load into Editor",
                        key="mc_load",
                        use_container_width=True,
                    ):
                        _load_into_editor(card_id)
        st.caption(
            "ℹ️ Only the card created in this browser session is shown here. "
            "Refreshing the page resets this view."
        )

    with tab_requests:
        if card_id is None:
            st.info(
                "Save a model card first, then submit it for publication review."
            )
        else:
            label, kind = _STATUS_DISPLAY.get(status, (status.title(), "info"))
            getattr(st, kind)(f"Publication status: **{label}**")

            if status == "draft":
                if st.button(
                    "Submit for Review",
                    key="mc_req_pub",
                    use_container_width=True,
                ):
                    try:
                        result = request_publication(card_id, token or "")
                        st.session_state.saved_publication_status = result.get(
                            "publication_status", "pending"
                        )
                        st.success("Submitted for review.")
                        st.rerun()
                    except BackendError as exc:
                        st.error(str(exc))

            elif status == "pending":
                st.info("Your model card is under review. No action needed.")

            elif status == "approved":
                st.success(
                    "Your model card is published and visible in the catalogue."
                )

            elif status == "rejected":
                st.error(
                    "Your submission was rejected. Save a new version with "
                    "corrections, then contact an admin to reset the status."
                )

    st.markdown("---")
    _, col_back, _ = st.columns([1, 2, 1])
    with col_back:
        if st.button("← Back to Main Page", key="my_cards_back_home", use_container_width=True):
            st.query_params["view"] = "home"
            st.rerun()


def _load_into_editor(card_id: int) -> None:
    """Fetch the latest version of card_id and open it in the editor."""
    from app.ui.screens.sections.card_metadata import (  # noqa: PLC0415
        card_metadata_render,
    )

    try:
        versions = get_versions(card_id)
    except BackendError as exc:
        st.error(str(exc))
        return

    if not versions:
        st.error("No versions found for this card.")
        return

    latest = next((v for v in versions if v.get("is_latest")), versions[-1])
    populate_session_state_from_json(latest["content_json"])
    st.session_state.runpage = card_metadata_render
    st.query_params["view"] = "create"
    st.rerun()
