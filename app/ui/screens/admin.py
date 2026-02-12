"""Admin panel — review and moderate publication requests.

Only accessible to users with is_admin=True.
Displays all versions currently in_review and lets the admin
approve or reject each one, with optional written feedback on rejection.

Preview workflow (per pending card):
  - "View Card" → loads the version content into the read-only viewer.
  - "Download PDF" → generates a PDF on-the-fly and offers a browser download.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from app.client.model_cards import (
    BackendError,
    approve_version_admin,
    get_version_admin,
    list_pending_admin,
    reject_version_admin,
)


def admin_page() -> None:
    """Render the admin moderation panel."""
    if not st.session_state.get("auth_token"):
        st.warning("You must be logged in to access the admin panel.")
        st.markdown("[Login](?view=login)", unsafe_allow_html=True)
        return

    if not st.session_state.get("auth_is_admin"):
        st.error("Access denied — admin privileges required.")
        return

    token: str = st.session_state["auth_token"]

    st.header("Admin Panel — Publication Requests")
    st.caption(
        "Review model card versions submitted for publication. "
        "Approved versions become publicly visible in the Published Model Cards gallery."
    )

    if st.button("↻ Refresh", key="admin_refresh"):
        st.rerun()

    st.divider()

    # Clean up stale PDF bytes stored from previous runs
    for _sk in [
        k for k in list(st.session_state.keys())
        if k.startswith("_admin_pdf_") and isinstance(st.session_state.get(k), (bytes, bytearray))
        and not any(k == f"_admin_pdf_{item.get('id')}" for item in st.session_state.get("_admin_pending", []))
    ]:
        del st.session_state[_sk]

    try:
        pending: list[dict[str, Any]] = list_pending_admin(token)
    except BackendError as exc:
        st.error(f"Could not load pending requests: {exc}")
        return

    # Cache the pending list for the stale-PDF cleanup above on next run
    st.session_state["_admin_pending"] = pending

    if not pending:
        st.success("No pending publication requests — all caught up.")
        _back_button()
        return

    st.markdown(f"**{len(pending)} request{'s' if len(pending) != 1 else ''} awaiting review**")
    st.markdown("<br>", unsafe_allow_html=True)

    for item in pending:
        _render_pending_item(item, token)

    _back_button()


def _load_version_readonly(version_id: int, token: str) -> None:
    """Fetch the version content and open it in the read-only card viewer."""
    from app.services.state_store import populate_session_state_from_json  # noqa: PLC0415
    from app.ui.screens.sections.card_metadata import card_metadata_render  # noqa: PLC0415

    try:
        version_data = get_version_admin(version_id, token)
    except BackendError as exc:
        st.error(str(exc))
        return

    content: dict[str, Any] = version_data.get("content") or {}
    populate_session_state_from_json(content)
    st.session_state["_view_mode"] = True  # read-only viewer
    st.session_state.runpage = card_metadata_render
    st.query_params["view"] = "create"
    st.rerun()


def _make_admin_pdf(version_id: int, token: str, slug: str, version: str) -> bytes | None:
    """Fetch version content and generate PDF bytes for the admin preview."""
    from app.services.markdown.renderer import render_version_pdf_bytes  # noqa: PLC0415

    try:
        version_data = get_version_admin(version_id, token)
    except BackendError as exc:
        st.error(str(exc))
        return None

    content: dict[str, Any] = version_data.get("content") or {}
    is_anonymous: bool = bool(version_data.get("is_anonymous", False))
    model_bi: dict[str, Any] = content.get("model_basic_information") or {}
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


def _render_pending_item(item: dict[str, Any], token: str) -> None:
    """Render a single pending version with preview and approve / reject controls."""
    version_id: int = item["id"]
    slug: str = item.get("slug", "—")
    task_type: str = item.get("task_type", "—")
    version: str = item.get("version", "—")
    submitted_date: str = str(item.get("created_at", ""))[:10]

    confirm_key = f"_admin_confirm_reject_{version_id}"
    feedback_key = f"_admin_feedback_{version_id}"
    pdf_state_key = f"_admin_pdf_{version_id}"

    with st.container(border=True):
        # ── Info row ──────────────────────────────────────────────────────────
        col_info, col_view, col_pdf, col_approve, col_reject = st.columns([3, 1, 1, 1, 1])

        with col_info:
            st.markdown(f"**{slug}**  `v{version}`")
            st.caption(f"Task: {task_type}  ·  Submitted: {submitted_date}")

        # ── View Card ─────────────────────────────────────────────────────────
        with col_view:
            if st.button(
                "View Card",
                key=f"admin_view_{version_id}",
                use_container_width=True,
                help="Open the model card in the read-only viewer",
            ):
                _load_version_readonly(version_id, token)

        # ── Download PDF ──────────────────────────────────────────────────────
        with col_pdf:
            if pdf_state_key in st.session_state:
                st.download_button(
                    "⬇ Save PDF",
                    data=st.session_state[pdf_state_key],
                    file_name=f"{slug}_v{version}.pdf",
                    mime="application/pdf",
                    key=f"admin_dl_pdf_{version_id}",
                    use_container_width=True,
                )
            else:
                if st.button(
                    "Preview PDF",
                    key=f"admin_pdf_btn_{version_id}",
                    use_container_width=True,
                    help="Generate a PDF preview of this model card",
                ):
                    with st.spinner("Generating PDF…"):
                        pdf_bytes = _make_admin_pdf(version_id, token, slug, version)
                    if pdf_bytes is not None:
                        st.session_state[pdf_state_key] = pdf_bytes
                        st.rerun()

        # ── Approve ───────────────────────────────────────────────────────────
        with col_approve:
            if st.button(
                "Approve",
                key=f"admin_approve_{version_id}",
                use_container_width=True,
                type="primary",
            ):
                try:
                    approve_version_admin(version_id, token)
                    st.success(f"**{slug}** v{version} approved and published.")
                except BackendError as exc:
                    st.error(str(exc))
                # Clear cached PDF on state change
                st.session_state.pop(pdf_state_key, None)
                st.rerun()

        # ── Reject (two-step with optional feedback) ──────────────────────────
        with col_reject:
            if not st.session_state.get(confirm_key):
                if st.button(
                    "Reject",
                    key=f"admin_reject_{version_id}",
                    use_container_width=True,
                ):
                    st.session_state[confirm_key] = True
                    st.rerun()

        if st.session_state.get(confirm_key):
            st.warning(
                f"Reject **{slug}** v{version}?  "
                "The submitter will be able to revise and resubmit."
            )
            st.text_area(
                "Feedback for the submitter (optional)",
                key=feedback_key,
                placeholder=(
                    "Explain what needs to be corrected before resubmission. "
                    "Leave blank to reject without a message."
                ),
                height=100,
            )
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button(
                    "Confirm Reject",
                    key=f"admin_confirm_reject_{version_id}",
                    use_container_width=True,
                    type="primary",
                ):
                    feedback: str = st.session_state.get(feedback_key, "") or ""
                    try:
                        reject_version_admin(version_id, token, feedback=feedback)
                        st.info(f"**{slug}** v{version} rejected.")
                    except BackendError as exc:
                        st.error(str(exc))
                    st.session_state.pop(confirm_key, None)
                    st.session_state.pop(feedback_key, None)
                    st.session_state.pop(pdf_state_key, None)
                    st.rerun()
            with col_no:
                if st.button(
                    "Cancel",
                    key=f"admin_cancel_reject_{version_id}",
                    use_container_width=True,
                ):
                    st.session_state.pop(confirm_key, None)
                    st.session_state.pop(feedback_key, None)
                    st.rerun()


def _back_button() -> None:
    st.markdown("---")
    _, col, _ = st.columns([1, 2, 1])
    with col:
        if st.button("← Back to Main Page", key="admin_back_home", use_container_width=True):
            st.query_params["view"] = "home"
            st.rerun()
