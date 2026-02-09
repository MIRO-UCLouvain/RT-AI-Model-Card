"""Published Model Cards catalogue screen."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.client.model_cards import (
    BackendError,
    get_public_version,
    get_versions,
    list_public_model_cards,
)
from app.services.state_store import populate_session_state_from_json
from app.ui.utils.css import inject_css

AUTH_CSS_PATH = Path(__file__).resolve().parent.parent / "static" / "auth.css"


def _make_version_pdf(card: dict) -> bytes | None:
    """Fetch full version data and return PDF bytes, or None on failure."""
    from app.services.markdown.renderer import render_version_pdf_bytes  # noqa: PLC0415

    version_id: int = card["id"]
    card_id: int = card["card_id"]

    try:
        version_data = get_public_version(version_id)
        all_versions = get_versions(card_id)
    except BackendError as exc:
        st.error(str(exc))
        return None

    content: dict = version_data.get("content") or {}
    model_bi: dict = content.get("model_basic_information") or {}

    model_name: str = model_bi.get("name") or card.get("slug", "Model Card")
    author: str = model_bi.get("developed_by_name") or "Anonymous"
    contact_email: str = model_bi.get("developed_by_email") or ""
    version_str: str = card.get("version", version_data.get("version", ""))
    published_date: str = str(card.get("created_at", ""))[:10]
    history = [v for v in all_versions if v.get("status") == "published"]

    try:
        return render_version_pdf_bytes(
            content,
            model_name=model_name,
            version=version_str,
            author=author,
            contact_email=contact_email,
            published_date=published_date,
            version_history=history,
        )
    except RuntimeError as exc:
        st.error(str(exc))
        return None


def _load_version_into_editor(card_id: int, version_id: int) -> None:
    """Fetch the specific published version and open it in the editor."""
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

    # Find the requested version; fall back to the last (most recent) one.
    target = next((v for v in versions if v.get("id") == version_id), versions[-1])
    content = target.get("content")

    if not isinstance(content, dict):
        st.error("Could not read model card content.")
        return

    populate_session_state_from_json(content)
    st.session_state.runpage = card_metadata_render
    st.query_params["view"] = "create"
    st.rerun()


def _status_badge(status: str) -> str:
    """Return a small coloured HTML badge for *status*."""
    colours = {
        "published": ("#2e7d32", "#e8f5e9"),
        "in_review": ("#e65100", "#fff3e0"),
    }
    bg, fg_text = colours.get(status, ("#1565c0", "#e3f2fd"))
    label = status.replace("_", " ").upper()
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
        st.markdown("---")
        _, col_back, _ = st.columns([1, 2, 1])
        with col_back:
            if st.button("← Back to Main Page", key="published_back_home_empty", use_container_width=True):
                st.query_params["view"] = "home"
                st.rerun()
        return

    # HTML grid — display only (no interactive Streamlit elements inside HTML)
    cards_html = '<div class="cards-grid">'
    for card in cards:
        badge = _status_badge(card.get("status", "published"))
        slug = card.get("slug", "—")
        task = card.get("task_type", "—")
        version = card.get("version", "—")
        created = str(card.get("created_at", ""))[:10]
        cards_html += (
            '<div class="card-item">'
            '<div style="display:flex;justify-content:space-between;align-items:flex-start">'
            f'<span class="card-item__slug">{slug}</span>{badge}'
            "</div>"
            f'<div class="card-item__meta">Task: {task} &nbsp;·&nbsp; Version: {version} &nbsp;·&nbsp; Published: {created}</div>'
            "</div>"
        )
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

    # Action buttons must be Streamlit widgets (cannot live inside injected HTML)
    st.markdown("---")
    num_cols = min(3, len(cards))
    cols = st.columns(num_cols)
    for i, card in enumerate(cards):
        version_id: int = card["id"]
        with cols[i % num_cols]:
            st.caption(f"{card.get('slug', '')} · v{card.get('version', '')}")

            col_load, col_pdf = st.columns(2)
            with col_load:
                if st.button(
                    "Load into Editor",
                    key=f"load_card_{version_id}",
                    use_container_width=True,
                ):
                    _load_version_into_editor(card["card_id"], version_id)

            with col_pdf:
                if st.button(
                    "Download PDF",
                    key=f"pdf_btn_{version_id}",
                    use_container_width=True,
                ):
                    with st.spinner("Generating PDF…"):
                        pdf_bytes = _make_version_pdf(card)
                    if pdf_bytes is not None:
                        st.session_state[f"_pdf_{version_id}"] = pdf_bytes

            cached = st.session_state.get(f"_pdf_{version_id}")
            if cached is not None:
                slug = card.get("slug", "model-card")
                ver = card.get("version", "1")
                st.download_button(
                    "Save PDF",
                    data=cached,
                    file_name=f"{slug}_v{ver}.pdf",
                    mime="application/pdf",
                    key=f"dl_pdf_{version_id}",
                    use_container_width=True,
                )

    st.markdown("---")
    _, col_back, _ = st.columns([1, 2, 1])
    with col_back:
        if st.button("← Back to Main Page", key="published_back_home", use_container_width=True):
            st.query_params["view"] = "home"
            st.rerun()
