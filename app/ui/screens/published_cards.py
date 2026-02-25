"""Published Model Cards catalogue screen."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.client.model_cards import (
    BackendError,
    get_public_version,
    list_public_model_cards,
)
from app.services.state_store import populate_session_state_from_json
from app.ui.utils.css import inject_css

AUTH_CSS_PATH = Path(__file__).resolve().parent.parent / "static" / "auth.css"


def _make_version_pdf(card: dict) -> bytes | None:
    """Fetch full version data and return PDF bytes, or None on failure."""
    from app.services.markdown.renderer import render_version_pdf_bytes  # noqa: PLC0415

    version_id: int = card["id"]

    try:
        version_data = get_public_version(version_id)
    except BackendError as exc:
        st.error(str(exc))
        return None

    content: dict = version_data.get("content") or {}
    model_bi: dict = content.get("model_basic_information") or {}
    is_anonymous: bool = bool(card.get("is_anonymous", False))

    author: str = "" if is_anonymous else (model_bi.get("developed_by_name") or "")
    contact_email: str = "" if is_anonymous else (model_bi.get("developed_by_email") or "")

    try:
        return render_version_pdf_bytes(
            content,
            author=author,
            contact_email=contact_email,
            is_anonymous=is_anonymous,
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
        target = get_public_version(version_id)
    except BackendError as exc:
        st.error(str(exc))
        return

    content = target.get("content")

    if not isinstance(content, dict):
        st.error("Could not read model card content.")
        return

    populate_session_state_from_json(content)
    st.session_state["_view_mode"] = True  # read-only viewer
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

    # Remove stale bytes that older code stored under "dl_pdf_N" — those keys
    # now belong exclusively to download widgets, so a bytes value there would
    # raise StreamlitValueAssignmentNotAllowedError.
    for _sk in [
        k for k in list(st.session_state.keys())
        if k.startswith("dl_pdf_") and isinstance(st.session_state.get(k), (bytes, bytearray))
    ]:
        del st.session_state[_sk]

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
            if st.button("← Back to Main Page", use_container_width=True):
                st.query_params["view"] = "home"
                st.rerun()
        return

    for card in cards:
        version_id: int = card["id"]
        slug = card.get("slug", "—")
        task = card.get("task_type", "—")
        version = card.get("version", "—")
        created = str(card.get("created_at", ""))[:10]
        status = card.get("status", "published")
        is_anon = card.get("is_anonymous", False)
        author_name: str = card.get("author_name") or ""
        author_email: str = card.get("author_email") or ""
        # State key for cached PDF bytes — intentionally different from the
        # download widget key (dl_pdf_N) so we never assign a value directly
        # to a widget-managed key, which would cause
        # StreamlitValueAssignmentNotAllowedError.
        pdf_state_key = f"_pdf_bytes_{version_id}"

        with st.container(border=True):
            # ── Title + status badge ──────────────────────────────────────
            st.markdown(
                f"**{slug}** &nbsp; {_status_badge(status)}",
                unsafe_allow_html=True,
            )

            # ── Metadata row ─────────────────────────────────────────────
            st.caption(f"Task: {task}  ·  Version: {version}  ·  Published: {created}")

            # ── Author row ────────────────────────────────────────────────
            if is_anon:
                st.caption("Author: *Anonymous*")
            else:
                author_display = author_name or "—"
                if author_email:
                    st.caption(f"Author: {author_display}  ·  Contact: {author_email}")
                else:
                    st.caption(f"Author: {author_display}")

            # ── Action buttons — kept inside the card ────────────────────
            col_view, col_pdf, _ = st.columns([2, 2, 3])

            with col_view:
                if st.button(
                    "View Card",
                    key=f"load_card_{version_id}",
                    use_container_width=True,
                ):
                    _load_version_into_editor(card["card_id"], version_id)

            with col_pdf:
                if pdf_state_key in st.session_state:
                    # PDF already generated — show the download button.
                    # Key dl_pdf_N is only ever registered here; we never
                    # assign to it via st.session_state, so no conflict.
                    st.download_button(
                        "⬇ Save PDF",
                        data=st.session_state[pdf_state_key],
                        file_name=f"{slug}_v{version}.pdf",
                        mime="application/pdf",
                        key=f"dl_pdf_{version_id}",
                        use_container_width=True,
                    )
                else:
                    if st.button(
                        "Download PDF",
                        key=f"pdf_btn_{version_id}",
                        use_container_width=True,
                    ):
                        with st.spinner("Generating PDF…"):
                            pdf_bytes = _make_version_pdf(card)
                        if pdf_bytes is not None:
                            # Store under a non-widget key, then rerun so the
                            # download button renders cleanly in a fresh cycle.
                            st.session_state[pdf_state_key] = pdf_bytes
                            st.rerun()

    st.markdown("---")
    _, col_back, _ = st.columns([1, 2, 1])
    with col_back:
        if st.button(
            "← Back to Main Page",
            key="back_home_from_published",
            use_container_width=True,
        ):
            st.query_params["view"] = "home"
            st.rerun()
