"""Appendix page for the Model Cards Writing Tool."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.services.uploads import (
    delete_appendix_item,
    ensure_upload_state,
    save_appendix_files,
)
from app.ui.utils.preview_file import preview_file
from app.ui.utils.typography import (
    light_header_italics,
    section_divider,
    subtitle,
    title,
)

__all__ = ["appendix_render"]

APPENDIX_TITLE = "Appendix"
APPENDIX_HELP = (
    "Files uploaded in the **Appendix** as well as files added in other "
    "sections will **not** appear when you load an incomplete model card.\n\n"
    "They are included only when you download:\n"
    "- the **ZIP with files**\n"
    "- the **ZIP with Model Card (`.json`) + files**\n"
    "- the **Model Card as `.pdf`**"
)
APPENDIX_SUBTITLE = "Attach any additional files you want to include in your model card."
APPENDIX_HINT = (
    "Upload any supporting files (PDFs, figures, CSVs, notes…). "
    "For fields that only accept a single image, upload additional figures here.\n\n"
    "Each file appears as a **numbered item** in the final document — "
    "file names are not shown. "
    "For each file you can:\n"
    "- Add a **description** so readers know what it contains.\n"
    "- Select the **section** and **subsection** it belongs to — "
    "this classification is reflected in the PDF export.\n\n"
    "**PDF export:** only images (PNG, JPG, JPEG, SVG) are rendered inline. "
    "All other file types are listed by name only.\n"
    "**ZIP download:** all uploaded files are included regardless of type."
)

# ── Section / subsection taxonomy ─────────────────────────────────────────────
_SECTION_PLACEHOLDER = "— Select a section (optional) —"
_SUBSECTION_PLACEHOLDER = "— Select a subsection (optional) —"
_OTHER = "Other"

# Extend this dict to add new sections or subsections without touching the UI code.
SECTION_SUBSECTIONS: dict[str, list[str]] = {
    "Card Metadata": [_OTHER],
    "Model Basic Information": [_OTHER],
    "Technical Specifications": [
        "Model Architecture Figure",
        "Model Pipeline Figure",
        _OTHER,
    ],
    "Training Data & Methodology Information": [
        "Training & Validation Loss Curves",
        "Data Distribution",
        _OTHER,
    ],
    "Evaluation Data, Methodology & Results": [
        "Evaluation Results Figure",
        "Metrics Visualization",
        _OTHER,
    ],
    "Considerations & Recommendations": [_OTHER],
}

_ALL_SECTIONS: list[str] = [_SECTION_PLACEHOLDER, *SECTION_SUBSECTIONS.keys()]

# ── Upload directory ───────────────────────────────────────────────────────────
UPLOAD_DIR = Path("uploads/appendix")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif"}


def _appendix_uploader_key() -> str:
    """Stable key that changes only when the global appendix nonce changes."""
    return f"appendix_uploader_{st.session_state.appendix_uploader_nonce}"


def _bump_appendix_uploader() -> None:
    """Force remount of the appendix uploader to clear selection after save."""
    st.session_state.appendix_uploader_nonce += 1


def _effective_subsection(file_data: dict[str, str]) -> str:
    """Return the subsection label to display, resolving 'Other' to custom text."""
    subsection = (file_data.get("subsection") or "").strip()
    custom = (file_data.get("subsection_custom") or "").strip()
    return custom if subsection == _OTHER else subsection


def _render_uploaded_row(
    item_idx: int,
    original_name: str,
    file_data: dict[str, str],
) -> None:
    """Display a numbered appendix item with section classification and preview.

    :param item_idx: 1-based item number shown to the user.
    :type item_idx: int
    :param original_name: Original filename (used as dict key; not displayed).
    :type original_name: str
    :param file_data: Metadata dict with ``path``, ``stored_name``,
        ``custom_label``, ``section``, ``subsection``, ``subsection_custom``.
    :type file_data: dict[str, str]
    """
    file_path = file_data["path"]
    custom_label = file_data.get("custom_label", "")
    section = (file_data.get("section") or "")
    subsection_display = _effective_subsection(file_data)

    # ── Numbered header ────────────────────────────────────────────────────
    header = f"**Item {item_idx}**"
    if custom_label:
        header += f": {custom_label}"
    st.markdown(header)

    # Section / subsection summary line (shown only when classified)
    if section:
        loc = section
        if subsection_display:
            loc += f" – {subsection_display}"
        st.caption(f"Section: {loc}")

    # ── Description + Delete ───────────────────────────────────────────────
    col_desc, col_del = st.columns([6, 1])
    with col_desc:
        label_val = st.text_input(
            label="Description",
            value=custom_label,
            key=f"label_{original_name}",
            placeholder="e.g., Supporting figure or table",
            label_visibility="collapsed",
            help="Short description shown in the final document.",
        )
        st.session_state.appendix_uploads[original_name]["custom_label"] = label_val

    with col_del:
        if st.button("Delete", key=f"del_{file_data['stored_name']}"):
            delete_appendix_item(original_name)
            st.rerun()

    # ── Section selector ───────────────────────────────────────────────────
    st.caption(
        "Optionally classify this file by section and type. "
        "This will be reflected in the appendix and PDF export."
    )
    section_idx = (
        _ALL_SECTIONS.index(section) if section in _ALL_SECTIONS else 0
    )
    section_val = st.selectbox(
        label="Section",
        options=_ALL_SECTIONS,
        index=section_idx,
        key=f"section_{original_name}",
    )
    new_section = section_val if section_val != _SECTION_PLACEHOLDER else ""
    st.session_state.appendix_uploads[original_name]["section"] = new_section

    # ── Subsection selector (progressive disclosure) ───────────────────────
    if new_section and new_section in SECTION_SUBSECTIONS:
        subsection_options = [_SUBSECTION_PLACEHOLDER, *SECTION_SUBSECTIONS[new_section]]

        stored_sub = (file_data.get("subsection") or "")
        # Reset subsection when section changes and stored value is no longer valid
        if stored_sub and stored_sub not in SECTION_SUBSECTIONS[new_section]:
            stored_sub = ""
            st.session_state.appendix_uploads[original_name]["subsection"] = ""
            st.session_state.pop(f"subsection_{original_name}", None)

        subsection_idx = (
            subsection_options.index(stored_sub)
            if stored_sub in subsection_options
            else 0
        )
        subsection_val = st.selectbox(
            label="Subsection",
            options=subsection_options,
            index=subsection_idx,
            key=f"subsection_{original_name}",
        )
        new_subsection = (
            subsection_val if subsection_val != _SUBSECTION_PLACEHOLDER else ""
        )
        st.session_state.appendix_uploads[original_name]["subsection"] = new_subsection

        # Free-text input when "Other" is chosen
        if new_subsection == _OTHER:
            custom_sub = st.text_input(
                label="Custom subsection",
                value=file_data.get("subsection_custom", ""),
                key=f"subsection_custom_{original_name}",
                placeholder="Describe the content of this file",
                help="This label will appear next to the section name in the document.",
            )
            st.session_state.appendix_uploads[original_name]["subsection_custom"] = (
                custom_sub
            )
        else:
            st.session_state.appendix_uploads[original_name]["subsection_custom"] = ""
    else:
        # No section selected — clear subsection state
        st.session_state.appendix_uploads[original_name]["subsection"] = ""
        st.session_state.appendix_uploads[original_name]["subsection_custom"] = ""

    # ── Preview ────────────────────────────────────────────────────────────
    suffix = Path(file_path).suffix.lower()
    if suffix in _IMAGE_SUFFIXES:
        try:
            st.image(file_path, use_container_width=True)
        except (OSError, TypeError, ValueError):
            light_header_italics("(Preview unavailable)")
        st.caption(original_name)
    else:
        with st.expander("Preview", expanded=False):
            prev = preview_file(file_path)
            if prev is False:
                light_header_italics("Preview not supported for this file type.")
            elif prev is None:
                light_header_italics("Could not preview this file.")

    section_divider()


def appendix_render() -> None:
    """
    Render the Appendix page.

    Shows the appendix title, help text, subtitle and hint; ensures
    upload-related session state, presents a file uploader (any file type,
    multiple files), persists uploaded files, and lists existing uploads with
    controls to set a description, section/subsection, preview, or delete each
    file. May mutate st.session_state and call st.rerun() when uploads change.
    """
    from app.ui.components.sidebar import sidebar_render  # noqa: PLC0415

    sidebar_render()

    title(APPENDIX_TITLE)
    st.info(APPENDIX_HELP, icon="ℹ")  # noqa: RUF001
    subtitle(APPENDIX_SUBTITLE)
    st.info(APPENDIX_HINT)

    ensure_upload_state()

    uploaded_files = st.file_uploader(
        "Upload files here",
        type=None,  # Allow any file type in Appendix
        accept_multiple_files=True,
        help="Any file type is allowed.",
        key=_appendix_uploader_key(),
    )

    if save_appendix_files(uploaded_files, UPLOAD_DIR):
        _bump_appendix_uploader()
        st.rerun()

    if st.session_state.appendix_uploads:
        title("Files Uploaded")
        section_divider()

        for idx, (original_name, file_data) in enumerate(
            list(st.session_state.appendix_uploads.items()), start=1
        ):
            _render_uploaded_row(idx, original_name, file_data)
