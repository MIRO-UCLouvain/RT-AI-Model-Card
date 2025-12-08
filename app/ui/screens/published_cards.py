"""Published Model Cards catalogue screen."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.client.model_cards import BackendError, get_versions, list_public_model_cards
from app.services.state_store import populate_session_state_from_json
from app.ui.utils.css import inject_css

AUTH_CSS_PATH = Path(__file__).resolve().parent.parent / "static" / "auth.css"


def _load_card_into_editor(card_id: int) -> None:
    """Fetch the latest version of *card_id* and open it in the editor."""
    from app.ui.screens.sections.card_metadata import (  # noqa: PLC0415
        card_metadata_render,
    )

    try:
        versions = get_versions(card_id)
    except BackendError as exc:
        st.error(str(exc))
        return

    if not versions:
        st.error("This model card has no versions yet.")
        return

    # Prefer the version flagged as latest; fall back to the last in the list.
    latest = next((v for v in versions if v.get("is_latest")), versions[-1])
    content_json = latest.get("content_json")

    if not isinstance(content_json, dict):
        st.error("Could not read model card content.")
        return

    populate_session_state_from_json(content_json)
    st.session_state.runpage = card_metadata_render
    # Navigate to the editor view
    st.query_params["view"] = "create"
    st.rerun()


def _status_badge(status: str) -> str:
    """Return a small coloured HTML badge for *status*."""
    colours = {
        "approved": ("#2e7d32", "#e8f5e9"),
    }
    bg, fg_text = colours.get(status, ("#1565c0", "#e3f2fd"))
    label = status.upper()
    return (
        f'<span style="background:{fg_text}; color:{bg}; '
        f'border:1px solid {bg}; border-radius:4px; '
        f'padding:2px 8px; font-size:0.75em; font-weight:600;">'
        f"{label}</span>"
    )


def published_cards_page() -> None:
    """Render the public catalogue of approved model cards."""
    inject_css(AUTH_CSS_PATH)

    st.header("Published Model Cards")
    st.markdown(
        "Browse model cards that have been reviewed and approved for publication."
    )

    try:
        cards = list_public_model_cards()
    except BackendError as exc:
        st.error(f"Could not load published cards: {exc}")
        return

    if not cards:
        st.info("No model cards have been published yet.")
        return

    # HTML grid — display only (no interactive Streamlit elements inside HTML)
    cards_html = '<div class="cards-grid">'
    for card in cards:
        badge = _status_badge(card.get("publication_status", "approved"))
        slug = card.get("slug", "—")
        task = card.get("task_type", "—")
        created = str(card.get("created_at", ""))[:10]
        cards_html += (
            '<div class="card-item">'
            '<div style="display:flex;justify-content:space-between;align-items:flex-start">'
            f'<span class="card-item__slug">{slug}</span>{badge}'
            "</div>"
            f'<div class="card-item__meta">Task: {task} &nbsp;·&nbsp; Published: {created}</div>'
            "</div>"
        )
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

    # Load buttons must be Streamlit widgets (cannot live inside injected HTML)
    st.markdown("---")
    num_cols = min(3, len(cards))
    cols = st.columns(num_cols)
    for i, card in enumerate(cards):
        with cols[i % num_cols]:
            st.caption(card.get("slug", ""))
            if st.button(
                "Load into Editor",
                key=f"load_card_{card['id']}",
                use_container_width=True,
            ):
                _load_card_into_editor(card["id"])

    st.markdown("---")
    _, col_back, _ = st.columns([1, 2, 1])
    with col_back:
        if st.button("← Back to Main Page", key="published_back_home", use_container_width=True):
            st.query_params["view"] = "home"
            st.rerun()
