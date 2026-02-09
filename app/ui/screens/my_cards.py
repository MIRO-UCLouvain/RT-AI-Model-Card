"""My Model Cards screen — persistent card management and publish requests.

Handles both ?view=my_cards and ?view=requests (alias).

All cards are loaded from the backend database, not from session state,
so they survive logout/login and browser reloads.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

from app.client.model_cards import (
    BackendError,
    compare_versions,
    delete_model_card,
    get_versions,
    list_model_cards,
    request_publication,
)
from app.services.state_store import clear_form_state, populate_session_state_from_json
from app.ui.utils.auth import clear_card_state, save_card_state
from app.ui.utils.css import inject_css

_DIFF_CSS_PATH = str(Path(__file__).parent.parent / "static" / "diff.css")

_STATUS_DISPLAY: dict[str, tuple[str, str]] = {
    "draft":     ("Draft — not submitted", "info"),
    "in_review": ("Under review",          "warning"),
    "published": ("Published ✓",           "success"),
    "rejected":  ("Rejected",              "error"),
}

# Friendly section titles for display (falls back to raw key if not listed)
_SECTION_LABELS: dict[str, str] = {
    "task":                                                 "Task",
    "card_metadata":                                        "Card Metadata",
    "model_basic_information":                              "Model Basic Information",
    "technical_specifications":                             "Technical Specifications",
    "training_data":                                        "Training Data",
    "evaluations":                                          "Evaluations",
    "other_considerations":                                 "Other Considerations",
}


# ── Main page ────────────────────────────────────────────────────────────────

def my_cards_page() -> None:
    """Render the My Model Cards screen with My Cards, Requests, and Compare tabs."""
    if not st.session_state.get("auth_token"):
        st.warning("You must be logged in to view your model cards.")
        st.markdown(
            "[Login](?view=login)  ·  [Register](?view=register)",
            unsafe_allow_html=True,
        )
        return

    st.header("My Model Cards")

    token: str = st.session_state.get("auth_token") or ""

    tab_cards, tab_requests, tab_compare = st.tabs(
        ["My Cards", "Requests to Publish", "Compare Versions"]
    )

    with tab_cards:
        _my_cards_tab(token)

    with tab_requests:
        _requests_tab(token)

    with tab_compare:
        _compare_tab(token)

    st.markdown("---")
    _, col_back, _ = st.columns([1, 2, 1])
    with col_back:
        if st.button("← Back to Main Page", key="my_cards_back_home", use_container_width=True):
            st.query_params["view"] = "home"
            st.rerun()


# ── My Cards tab ──────────────────────────────────────────────────────────────

def _my_cards_tab(token: str) -> None:
    """Show all cards the user has ever saved, fetched from the backend."""
    try:
        cards = list_model_cards(token)
    except BackendError as exc:
        st.error(f"Could not load your model cards: {exc}")
        return

    if not cards:
        st.info("No model cards saved yet.")
        st.markdown(
            "Start by [creating a model card](?view=create) "
            "and saving it from the sidebar.",
            unsafe_allow_html=True,
        )
        return

    for card in cards:
        card_id: int = card["id"]
        slug: str = card.get("slug", "—") or "—"

        # Fetch versions directly — more reliable than the embedded list in
        # list_model_cards (which depends on SQLAlchemy selectinload).
        try:
            versions: list[dict[str, Any]] = get_versions(card_id)
        except BackendError:
            versions = []
        latest = versions[-1] if versions else None

        confirm_key = f"_confirm_delete_{card_id}"

        with st.container(border=True):
            col_info, col_load, col_delete = st.columns([4, 1, 1])

            with col_info:
                st.markdown(f"**{slug}**")
                if latest:
                    ver_str = latest.get("version", "?")
                    status_raw: str = latest.get("status", "draft")
                    label, _ = _STATUS_DISPLAY.get(status_raw, (status_raw.title(), "info"))
                    created = str(latest.get("created_at", ""))[:10]
                    st.caption(f"Latest: v{ver_str} · {label} · saved {created}")
                    n = len(versions)
                    st.caption(f"{n} version{'s' if n != 1 else ''} total")
                else:
                    st.caption("No versions found for this card.")

            with col_load:
                if st.button(
                    "Load into Editor",
                    key=f"load_{card_id}",
                    use_container_width=True,
                    help="Open the latest version of this card in the editor",
                ):
                    _load_into_editor(card_id, slug)

            with col_delete:
                if not st.session_state.get(confirm_key):
                    if st.button(
                        "Delete",
                        key=f"del_{card_id}",
                        use_container_width=True,
                        help="Permanently delete this card and all its versions",
                    ):
                        st.session_state[confirm_key] = True
                        st.rerun()

            if st.session_state.get(confirm_key):
                st.warning(
                    f"Delete **{slug}** and all its versions? This cannot be undone."
                )
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button(
                        "Confirm Delete",
                        key=f"confirm_del_{card_id}",
                        use_container_width=True,
                        type="primary",
                    ):
                        try:
                            delete_model_card(card_id, token)
                            # If this was the active card in the editor, clear it.
                            if st.session_state.get("saved_card_id") == card_id:
                                clear_card_state()
                        except BackendError as exc:
                            st.error(str(exc))
                        st.session_state.pop(confirm_key, None)
                        st.rerun()
                with col_no:
                    if st.button(
                        "Cancel",
                        key=f"cancel_del_{card_id}",
                        use_container_width=True,
                    ):
                        st.session_state.pop(confirm_key, None)
                        st.rerun()


# ── Requests tab ──────────────────────────────────────────────────────────────

def _requests_tab(token: str) -> None:
    """Render all versions across all user cards with their publication statuses."""
    if not token:
        st.info("Save a model card first, then submit it for publication review.")
        return

    try:
        cards = list_model_cards(token)
    except BackendError as exc:
        st.error(f"Could not load your model cards: {exc}")
        return

    if not cards:
        st.info("Save a model card first, then submit it for publication review.")
        return

    any_version = False
    for card in cards:
        slug = card.get("slug", "—")
        card_id: int = card["id"]

        # Fetch versions directly — same reliable source used by Compare Versions.
        try:
            versions = get_versions(card_id)
        except BackendError:
            versions = []
        if not versions:
            continue
        any_version = True

        st.markdown(f"#### {slug}")
        for ver in versions:
            ver_id: int = ver["id"]
            ver_str: str = ver.get("version", "?")
            status: str = ver.get("status", "draft")
            created: str = str(ver.get("created_at", ""))[:10]

            label, kind = _STATUS_DISPLAY.get(status, (status.title(), "info"))

            with st.container(border=True):
                col_info, col_action = st.columns([3, 1])
                with col_info:
                    st.markdown(f"**Version {ver_str}** · saved {created}")
                    getattr(st, kind)(f"Status: **{label}**")

                with col_action:
                    if status in ("draft", "rejected"):
                        if st.button(
                            "Submit for Review",
                            key=f"req_pub_{ver_id}",
                            use_container_width=True,
                        ):
                            try:
                                all_versions = get_versions(card_id)
                                published = [
                                    v for v in all_versions
                                    if v.get("status") == "published"
                                    and v["id"] != ver_id
                                ]
                                if published:
                                    last_pub = published[-1]
                                    try:
                                        diff = compare_versions(
                                            card_id, last_pub["id"], ver_id
                                        )
                                        st.session_state["_diff_before_submit"] = diff
                                    except BackendError:
                                        st.session_state["_diff_before_submit"] = None
                                else:
                                    st.session_state["_diff_before_submit"] = None
                            except BackendError:
                                st.session_state["_diff_before_submit"] = None
                            st.session_state["_pending_submit_card_id"] = card_id
                            st.session_state["_pending_submit_ver_id"] = ver_id
                            st.session_state["_show_submit_dialog"] = True

                    elif status == "in_review":
                        st.caption("Under review — editing locked.")
                    elif status == "published":
                        st.caption("Published ✓")

        st.divider()

    if not any_version:
        st.info("No versions found. Save a model card from the editor first.")

    if st.session_state.get("_show_submit_dialog"):
        _pending_card_id: int | None = st.session_state.get("_pending_submit_card_id")
        _pending_ver_id: int | None = st.session_state.get("_pending_submit_ver_id")
        if _pending_card_id is not None and _pending_ver_id is not None:
            _submit_diff_dialog(_pending_card_id, _pending_ver_id, token)


# ── Compare tab ───────────────────────────────────────────────────────────────

def _compare_tab(token: str) -> None:
    """Render the version comparison tab — works for any of the user's cards."""
    try:
        cards = list_model_cards(token)
    except BackendError as exc:
        st.error(f"Could not load your model cards: {exc}")
        return

    if not cards:
        st.info("Save a model card first to compare versions.")
        return

    # Card selector (shown only when user has more than one card)
    if len(cards) > 1:
        card_labels = [
            f"{c.get('slug', '—')} (id {c['id']})" for c in cards
        ]
        selected_label = st.selectbox(
            "Select a card",
            options=card_labels,
            key="diff_card_sel",
        )
        selected_idx = card_labels.index(selected_label)
        card = cards[selected_idx]
    else:
        card = cards[0]

    card_id: int = card["id"]

    try:
        versions: list[dict[str, Any]] = get_versions(card_id)
    except BackendError as exc:
        st.error(f"Could not load versions: {exc}")
        return

    if len(versions) < 2:
        st.info(
            "You need at least two saved versions to compare. "
            "Save a new version from the editor to enable comparison."
        )
        return

    version_labels = [
        f"v{v['version']}  (saved {str(v.get('created_at', ''))[:10]})"
        for v in versions
    ]
    version_ids = [v["id"] for v in versions]

    col_old, col_new = st.columns(2)
    with col_old:
        old_label = st.selectbox(
            "Old version",
            options=version_labels,
            index=0,
            key="diff_old_sel",
        )
    with col_new:
        new_label = st.selectbox(
            "New version",
            options=version_labels,
            index=len(version_labels) - 1,
            key="diff_new_sel",
        )

    old_idx = version_labels.index(old_label)
    new_idx = version_labels.index(new_label)
    old_id = version_ids[old_idx]
    new_id = version_ids[new_idx]

    if st.button("Compare", key="btn_compare", use_container_width=False):
        if old_id == new_id:
            st.warning("Select two different versions to compare.")
            return
        try:
            diff = compare_versions(card_id, old_id, new_id)
            st.session_state["_diff_result"] = diff
        except BackendError as exc:
            st.error(str(exc))
            st.session_state.pop("_diff_result", None)

    diff_result: dict[str, Any] | None = st.session_state.get("_diff_result")
    if diff_result:
        _render_diff(diff_result)


def _render_diff(diff: dict[str, Any]) -> None:
    """Render the structured diff returned by the backend."""
    inject_css(_DIFF_CSS_PATH)

    old_v = diff.get("old_version", "?")
    new_v = diff.get("new_version", "?")
    sections: dict[str, Any] = diff.get("sections", {})

    st.markdown(f"### Comparing **v{old_v}** → **v{new_v}**")

    if not sections:
        st.markdown(
            '<div class="diff-no-changes">✓ No differences found between these two versions.</div>',
            unsafe_allow_html=True,
        )
        return

    total_added = sum(len(s.get("added", [])) for s in sections.values())
    total_removed = sum(len(s.get("removed", [])) for s in sections.values())
    total_changed = sum(len(s.get("changed", [])) for s in sections.values())

    pills: list[str] = []
    if total_added:
        pills.append(f'<span class="diff-pill diff-pill--added">+ {total_added} added</span>')
    if total_removed:
        pills.append(f'<span class="diff-pill diff-pill--removed">− {total_removed} removed</span>')
    if total_changed:
        pills.append(f'<span class="diff-pill diff-pill--changed">~ {total_changed} changed</span>')
    if not pills:
        pills.append('<span class="diff-pill diff-pill--none">No changes</span>')

    st.markdown(
        f'<div class="diff-summary">{"".join(pills)}</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    for section_key, section_data in sections.items():
        added = section_data.get("added", [])
        removed = section_data.get("removed", [])
        changed = section_data.get("changed", [])

        if not (added or removed or changed):
            continue

        section_title = _SECTION_LABELS.get(section_key, section_key.replace("_", " ").title())
        n_changes = len(added) + len(removed) + len(changed)

        badge_parts: list[str] = []
        if added:
            badge_parts.append(
                f'<span class="diff-badge__item diff-badge__item--added">+{len(added)}</span>'
            )
        if removed:
            badge_parts.append(
                f'<span class="diff-badge__item diff-badge__item--removed">−{len(removed)}</span>'
            )
        if changed:
            badge_parts.append(
                f'<span class="diff-badge__item diff-badge__item--changed">~{len(changed)}</span>'
            )

        header_html = (
            f'<div class="diff-section-header">'
            f'<span>{section_title}</span>'
            f'<span class="diff-badge">{"".join(badge_parts)}</span>'
            f'</div>'
        )

        label = f"{section_title}  ({n_changes} change{'s' if n_changes != 1 else ''})"
        with st.expander(label, expanded=True):
            st.markdown(header_html, unsafe_allow_html=True)

            if added:
                st.markdown(
                    '<div class="diff-bucket-heading diff-bucket-heading--added">+ Added</div>',
                    unsafe_allow_html=True,
                )
                rows = "".join(
                    f'<div class="diff-row diff-row--added">'
                    f'<span class="diff-row__field">{_esc(item.get("field", ""))}</span>'
                    f'<span class="diff-row__value">{_format_value(item.get("value"))}</span>'
                    f'</div>'
                    for item in added
                )
                st.markdown(rows, unsafe_allow_html=True)

            if removed:
                st.markdown(
                    '<div class="diff-bucket-heading diff-bucket-heading--removed">− Removed</div>',
                    unsafe_allow_html=True,
                )
                rows = "".join(
                    f'<div class="diff-row diff-row--removed">'
                    f'<span class="diff-row__field">{_esc(item.get("field", ""))}</span>'
                    f'<span class="diff-row__value">{_format_value(item.get("value"))}</span>'
                    f'</div>'
                    for item in removed
                )
                st.markdown(rows, unsafe_allow_html=True)

            if changed:
                st.markdown(
                    '<div class="diff-bucket-heading diff-bucket-heading--changed">~ Changed</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="diff-sbs-labels">'
                    '<span></span><span>Before</span><span>After</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                rows = "".join(
                    f'<div class="diff-sbs">'
                    f'<span class="diff-sbs__field">{_esc(item.get("field", ""))}</span>'
                    f'<span class="diff-sbs__old">{_format_value(item.get("old"))}</span>'
                    f'<span class="diff-sbs__new">{_format_value(item.get("new"))}</span>'
                    f'</div>'
                    for item in changed
                )
                st.markdown(rows, unsafe_allow_html=True)


def _esc(text: str) -> str:
    """HTML-escape a plain string."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _format_value(value: Any) -> str:
    """Convert any diff value to a short, readable HTML string."""
    if value is None:
        return '<span class="diff-row__value--empty">(empty)</span>'
    if isinstance(value, str):
        escaped = _esc(value)
        if len(escaped) > 200:
            return escaped[:200] + "…"
        return escaped
    if isinstance(value, (dict, list)):
        import json  # noqa: PLC0415
        text = json.dumps(value, ensure_ascii=False)
        if len(text) > 200:
            text = text[:200] + "…"
        return _esc(text)
    return _esc(str(value))


# ── Submit confirmation dialog ────────────────────────────────────────────────

@st.dialog("Changes Before Submitting", width="large")
def _submit_diff_dialog(card_id: int, version_id: int, token: str) -> None:
    """Modal: show diff vs last published version, then confirm or cancel."""
    inject_css(_DIFF_CSS_PATH)
    diff: dict[str, Any] | None = st.session_state.get("_diff_before_submit")

    if diff is None:
        st.info(
            "No previous published version found — "
            "this will be the first published version of this card."
        )
    elif diff.get("sections"):
        st.markdown("**Changes compared to last published version:**")
        _render_diff(diff)
    else:
        st.markdown(
            '<div class="diff-no-changes">✓ No content differences compared to last published version.</div>',
            unsafe_allow_html=True,
        )

    st.divider()
    col_submit, col_cancel = st.columns(2)
    with col_submit:
        if st.button(
            "Confirm & Submit",
            type="primary",
            use_container_width=True,
            key="dialog_confirm_submit",
        ):
            try:
                result = request_publication(card_id, version_id, token)
                if st.session_state.get("saved_version_id") == version_id:
                    st.session_state.saved_version_status = result.get("status", "in_review")
                for key in ("_show_submit_dialog", "_diff_before_submit",
                            "_pending_submit_card_id", "_pending_submit_ver_id"):
                    st.session_state.pop(key, None)
            except BackendError as exc:
                st.error(str(exc))
                return
            st.rerun()
    with col_cancel:
        if st.button("Cancel", use_container_width=True, key="dialog_cancel_submit"):
            for key in ("_show_submit_dialog", "_diff_before_submit",
                        "_pending_submit_card_id", "_pending_submit_ver_id"):
                st.session_state.pop(key, None)
            st.rerun()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_into_editor(card_id: int, slug: str) -> None:
    """Fetch the latest version of card_id, clear editor state, then open in editor."""
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

    # Clear any existing editor state before loading so there is no leakage.
    clear_form_state()

    latest = versions[-1]
    populate_session_state_from_json(latest["content"])

    ver_str: str = latest["version"]
    status_str: str = latest.get("status", "draft")

    # Sync version metadata so the sidebar reflects the correct state.
    st.session_state.saved_card_id = card_id
    st.session_state.saved_version_id = latest["id"]
    st.session_state.saved_version = ver_str
    st.session_state.saved_version_status = status_str

    # Persist to cookies so the sidebar context survives a page reload.
    save_card_state(card_id=card_id, version=ver_str, slug=slug, status=status_str)

    st.session_state.runpage = card_metadata_render
    st.query_params["view"] = "create"
    st.rerun()
