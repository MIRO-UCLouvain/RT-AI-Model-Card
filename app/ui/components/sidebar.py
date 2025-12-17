"""Module Sidebar of the Model Card UI (refactored, same functionality)."""

from __future__ import annotations

import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any

import streamlit as st

from app.client.model_cards import (
    BackendError,
    create_model_card,
    create_version,
)
from app.ui.utils.auth import save_card_state
from app.services.state_store import clear_form_state
from app.core.model_card.constants import SCHEMA
from app.services.markdown.renderer import render_full_model_card_md
from app.services.schema_loader import get_model_card_schema
from app.services.serialization import parse_into_json
from app.services.validation import validate_required_fields
from app.ui.screens.sections.appendix import appendix_render
from app.ui.screens.sections.card_metadata import card_metadata_render
from app.ui.screens.sections.evaluation_data_mrc import (
    evaluation_data_mrc_render,
)
from app.ui.screens.sections.model_basic_information import (
    model_basic_information_render,
)
from app.ui.screens.sections.model_card_info import model_card_info_render
from app.ui.screens.sections.other_considerations import (
    other_considerations_render,
)
from app.ui.screens.sections.technical_specifications import (
    technical_specifications_render,
)
from app.ui.screens.sections.training_data import training_data_render
from app.ui.screens.sections.warnings import warnings_render
from app.ui.utils.css import inject_css

model_card_schema: dict[str, Any] = get_model_card_schema()

st.set_page_config(layout="wide", initial_sidebar_state="expanded")

SIDEBAR_WIDTH_PX: int = 500

# Location of the external CSS file
CSS_PATH = (Path(__file__).resolve().parent.parent / "static" / "sidebar.css")


# ── Navigation ────────────────────────────────────────────────────────────────

def _render_menu() -> None:  # noqa: C901
    if st.button("About Model Cards", use_container_width=True):
        st.session_state.runpage = model_card_info_render
        st.rerun()

    task = st.session_state.get("task", "Image-to-Image translation")
    missing = validate_required_fields(model_card_schema, current_task=task)
    warn_count = (
        len(missing)
        if isinstance(missing, (list, tuple))
        else (1 if missing else 0)
    )

    if warn_count:
        if st.button(
            "Check Warnings",
            key="btn_check_warnings",
            use_container_width=True,
            help="Open the list of missing required fields",
        ):
            st.session_state.runpage = warnings_render
            st.rerun()

        st.divider()

    st.markdown("## Menu")

    if st.button("Card Metadata", use_container_width=True):
        st.session_state.runpage = card_metadata_render
        st.rerun()

    if st.button("Model Basic Information", use_container_width=True):
        st.session_state.runpage = model_basic_information_render
        st.rerun()

    if st.button("Technical Specifications", use_container_width=True):
        st.session_state.runpage = technical_specifications_render
        st.rerun()

    if st.button(
        "Training Data, Methodology and Information",
        use_container_width=True,
    ):
        st.session_state.runpage = training_data_render
        st.rerun()

    if st.button(
        "Evaluation Data, Methodology, Results and Commissioning",
        use_container_width=True,
    ):
        st.session_state.runpage = evaluation_data_mrc_render
        st.rerun()

    if st.button("Other Considerations", use_container_width=True):
        st.session_state.runpage = other_considerations_render
        st.rerun()

    if st.button("Appendix", use_container_width=True):
        st.session_state.runpage = appendix_render
        st.rerun()


# ── Local downloads tab ────────────────────────────────────────────────────────

def _error_if_format_invalid() -> bool:
    if st.session_state.get("format_error"):
        st.error("Cannot download — fields have invalid format.")
        return True
    return False


def _show_required_missing(task: str | None) -> None:
    missing = validate_required_fields(model_card_schema, current_task=task)
    if missing:
        st.error(
            "Some required fields are missing. Check the Warnings "
            "section on the sidebar for details.",
        )


def _download_json_ui() -> None:
    with st.form("form_download_json"):
        if st.form_submit_button("Download Model Card as `.json`"):
            if _error_if_format_invalid():
                return
            _show_required_missing(st.session_state.get("task"))
            st.session_state.download_ready = True

    if st.session_state.get("download_ready"):
        card_content = parse_into_json(SCHEMA)
        st.download_button(
            "Your download is ready — click here (JSON)",
            data=card_content,
            file_name="model_card.json",
            mime="application/json",
            key="btn_download_json",
        )
        st.session_state.download_ready = False


def _download_pdf_ui() -> None:
    with st.form("form_download_pdf"):
        if st.form_submit_button("Download Model Card as `.pdf`"):
            if _error_if_format_invalid():
                return
            try:
                from app.services.markdown.renderer import (  # noqa: PLC0415
                    save_model_card_pdf,
                )

                pdf_path = save_model_card_pdf(
                    "model_card.pdf",
                    base_url=str(Path.cwd()),
                )
                st.session_state.download_ready_pdf = True
                st.session_state.generated_pdf_path = pdf_path
            except (ImportError, OSError, RuntimeError) as e:
                st.error(f"Failed to generate PDF: {e}")
                st.session_state.download_ready_pdf = False

    if st.session_state.get("download_ready_pdf"):
        pdf_path_raw = st.session_state.get(
            "generated_pdf_path",
            "model_card.pdf",
        )
        pdf_path_obj = Path(str(pdf_path_raw))
        with pdf_path_obj.open("rb") as pdf_file:
            st.download_button(
                "Your download is ready — click here (PDF)",
                pdf_file,
                file_name="model_card.pdf",
                use_container_width=True,
                key="btn_download_pdf",
            )
        st.session_state.download_ready_pdf = False


def _download_md_ui() -> None:
    def _parse_into_markdown() -> str:
        return render_full_model_card_md()

    with st.form("form_download_md"):
        if st.form_submit_button("Download Model Card as `.md`"):
            if _error_if_format_invalid():
                return
            _show_required_missing(st.session_state.get("task"))
            st.session_state.download_ready_md = True

    if st.session_state.get("download_ready_md"):
        try:
            md_text = _parse_into_markdown()
            with st.expander("Preview (.md)", expanded=False):
                st.code(md_text, language="markdown")
            st.download_button(
                "Your download is ready — click here (Markdown)",
                data=md_text.encode("utf-8"),
                file_name="model_card.md",
                mime="text/markdown",
                key="btn_download_md",
            )
        except (RuntimeError, OSError, ValueError) as e:
            st.error(f"Error while generating Markdown: {e}")
        finally:
            st.session_state.download_ready_md = False


def _get_uploaded_paths() -> list[str]:
    paths = st.session_state.get("all_uploaded_paths", set())
    return [p for p in list(paths) if isinstance(p, str) and Path(p).exists()]


def _build_original_name_map() -> dict[str, str]:
    """Return a mapping of stored file path → original file name.

    Sources:
    - ``render_uploads``: per-field uploads; ``meta["name"]`` is the
      sanitized original filename.
    - ``appendix_uploads``: the dict key IS the sanitized original filename.

    Duplicate original names are disambiguated by inserting a counter before
    the extension: ``figure.png``, ``figure (1).png``, ``figure (2).png``.
    """
    path_to_name: dict[str, str] = {}
    seen: dict[str, int] = {}

    def _unique(name: str) -> str:
        if name not in seen:
            seen[name] = 0
            return name
        seen[name] += 1
        stem, suffix = Path(name).stem, Path(name).suffix
        return f"{stem} ({seen[name]}){suffix}"

    # Field uploads
    for meta in st.session_state.get("render_uploads", {}).values():
        path = meta.get("path", "")
        name = meta.get("name", "")
        if path and name:
            path_to_name[path] = _unique(name)

    # Appendix uploads (key = sanitized original name)
    for original_name, data in st.session_state.get("appendix_uploads", {}).items():
        path = data.get("path", "")
        if path and original_name:
            path_to_name[path] = _unique(original_name)

    return path_to_name


def _download_files_zip_only_ui() -> None:
    with st.form("form_download_files"):
        if st.form_submit_button("Download files (`.zip`)"):
            files = _get_uploaded_paths()
            if not files:
                st.warning("No uploaded files to download.")
            else:
                st.session_state.download_files_ready = True

    if st.session_state.get("download_files_ready"):
        files = _get_uploaded_paths()
        if not files:
            st.warning("No uploaded files to download.")
        else:
            buffer = io.BytesIO()
            valid_files: list[str] = []
            for fpath in files:
                p = Path(fpath)
                if p.exists() and p.is_file():
                    valid_files.append(fpath)
                else:
                    st.warning(
                        f"Could not add (missing or not a file): {fpath}",
                    )
            if not valid_files:
                st.warning(
                    "No valid uploaded files to include in the ZIP.",
                )
            else:
                name_map = _build_original_name_map()
                with zipfile.ZipFile(
                    buffer,
                    "w",
                    compression=zipfile.ZIP_DEFLATED,
                ) as zf:
                    for fpath in valid_files:
                        arcname = name_map.get(fpath, Path(fpath).name)
                        zf.write(fpath, arcname=arcname)
                buffer.seek(0)
                st.download_button(
                    label="Download all files (ZIP)",
                    data=buffer,
                    file_name="uploaded_files.zip",
                    mime="application/zip",
                    key="btn_download_files_zip",
                    use_container_width=True,
                )
        st.session_state.download_files_ready = False


def _download_zip_json_plus_files_ui() -> None:
    with st.form("form_download_zip_all"):
        if st.form_submit_button(
            "Download `.zip` (Model Card `.json` + files)",
        ):
            files = _get_uploaded_paths()
            if not files:
                st.warning("No uploaded files to include in the ZIP.")
            elif _error_if_format_invalid():
                pass
            else:
                _show_required_missing(st.session_state.get("task"))
                st.session_state.download_zip_ready = True

    if st.session_state.get("download_zip_ready"):
        files = _get_uploaded_paths()
        if not files:
            st.warning("No uploaded files to include in the ZIP.")
        else:
            card_content = parse_into_json(SCHEMA)
            buffer = io.BytesIO()
            valid_files_zip: list[str] = []
            for fpath in files:
                p = Path(fpath)
                if p.exists() and p.is_file():
                    valid_files_zip.append(fpath)
                else:
                    st.warning(
                        f"Could not add (missing or not a file): {fpath}",
                    )
            try:
                name_map = _build_original_name_map()
                with zipfile.ZipFile(
                    buffer,
                    "w",
                    compression=zipfile.ZIP_DEFLATED,
                ) as zf:
                    zf.writestr("model_card.json", card_content)
                    for fpath in valid_files_zip:
                        original = name_map.get(fpath, Path(fpath).name)
                        arcname = f"files/{original}"
                        zf.write(fpath, arcname=arcname)
                buffer.seek(0)
                st.download_button(
                    "Your download is ready — click here (ZIP)",
                    data=buffer,
                    file_name="model_card_with_files.zip",
                    mime="application/zip",
                    key="btn_download_zip_all",
                    use_container_width=True,
                )
            except (OSError, RuntimeError, ValueError) as e:
                st.error(f"Failed to create ZIP: {e}")
        st.session_state.download_zip_ready = False


def _local_downloads_tab() -> None:
    st.markdown("## Download Model Card")
    with st.expander("Download Options", expanded=True):
        _download_json_ui()
        _download_pdf_ui()
        _download_md_ui()
        _download_files_zip_only_ui()
        _download_zip_json_plus_files_ui()


# ── Save section ──────────────────────────────────────────────────────────────

def _derive_slug(name: str) -> str:
    """Convert a model name to a URL-safe slug."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "my-model-card"


def _save_section() -> None:
    """Auth-gated save controls above the download tabs."""
    token: str | None = st.session_state.get("auth_token")
    if not token:
        st.info("[Sign in](?view=login) to save and publish your model card.")
        return

    st.markdown("## Save")
    card_id: int | None = st.session_state.get("saved_card_id")
    version: int | None = st.session_state.get("saved_version")

    if card_id is not None:
        st.caption(f"Saved · ID {card_id} · version {version}")
    else:
        st.caption("Not yet saved.")

    model_name: str = st.session_state.get(
        "model_basic_information_name", ""
    ) or ""
    task_type: str = st.session_state.get("task", "Other") or "Other"

    slug = st.text_input(
        "Slug (unique identifier)",
        value=_derive_slug(model_name),
        key="saved_slug",
        disabled=card_id is not None,
        help="URL-safe name, e.g. my-segmentation-model. Cannot change after first save.",
    )
    title = st.text_input(
        "Version title",
        value=model_name,
        key="saved_title",
        help="Short description for this version.",
    )

    clean_slug = _derive_slug(slug)
    if clean_slug != slug and slug:
        st.caption(f"Slug will be saved as: **{clean_slug}**")

    label = "Save new version" if card_id is not None else "Save"
    if st.button(label, use_container_width=True, key="btn_save"):
        try:
            content: dict = json.loads(parse_into_json(SCHEMA))
            if card_id is None:
                result = create_model_card(
                    slug=clean_slug,
                    task_type=task_type,
                    title=title or clean_slug,
                    content=content,
                )
                st.session_state.saved_card_id = result["id"]
                st.session_state.saved_publication_status = result.get(
                    "publication_status", "draft"
                )
                saved_version = result["versions"][0]["version_number"]
            else:
                result = create_version(
                    card_id=card_id,
                    title=title or clean_slug,
                    content=content,
                )
                saved_version = result["version_number"]
            st.session_state.saved_version = saved_version
            # Persist card identifiers to browser cookies so they survive page reloads
            save_card_state(
                card_id=st.session_state.saved_card_id,
                version=saved_version,
                slug=clean_slug,
                status=st.session_state.get("saved_publication_status", "draft"),
            )
            st.success(f"Saved as version {saved_version}.")
            st.rerun()
        except BackendError as exc:
            msg = str(exc)
            st.error(msg)
            if "already exists" in msg:
                st.info(
                    "A card with this slug was saved in a previous session. "
                    "Change the slug to create a new card, or reload the page "
                    "if you want to add a new version to the existing one."
                )
        except (ValueError, KeyError, TypeError) as exc:
            st.error(f"Unexpected error: {exc}")


# ── GitHub badge ──────────────────────────────────────────────────────────────

def _render_github_repo(repo_url: str) -> None:
    """Render a GitHub repository link with a badge (centered card-style)."""
    st.markdown(
        f"""
        <div style="text-align: center; padding: 1.2em; border: 1px solid #ddd;
                    border-radius: 10px; background-color: #ffffff;">
            <p style="font-size: 1.1em;">
                This project is <strong>open-source</strong>.
                Explore the code, report issues, or contribute on GitHub.
                Feel free to star the repository if you find it useful!
            </p>
            <a href="{repo_url}" target="_blank">
                <img src="https://img.shields.io/badge/GitHub-Repository-181717?logo=github&logoColor=white"
                     alt="GitHub Repository"/>
            </a>
            <a href="{repo_url}/stargazers" target="_blank">
                <img src="https://img.shields.io/github/stars/{repo_url.split('github.com/')[-1]}?style=social"
                     alt="GitHub Stars"/>
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Entry point ───────────────────────────────────────────────────────────────

def sidebar_render() -> None:
    """Render the sidebar for the Streamlit app."""
    with st.sidebar:
        inject_css(CSS_PATH)

        # ── Back to Main Page (top of sidebar, always visible) ────────────────
        if not st.session_state.get("_sidebar_confirm_back"):
            if st.button(
                "← Back to Main Page",
                key="sidebar_back_home",
                use_container_width=True,
            ):
                st.session_state["_sidebar_confirm_back"] = True
                st.rerun()
        else:
            st.warning(
                "All unsaved data will be lost. "
                "Download your card before leaving."
            )
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("Leave", key="sidebar_confirm_leave", use_container_width=True):
                    st.session_state.pop("_sidebar_confirm_back", None)
                    clear_form_state()
                    st.query_params["view"] = "home"
                    st.rerun()
            with col_no:
                if st.button("Stay", key="sidebar_cancel_leave", use_container_width=True):
                    st.session_state.pop("_sidebar_confirm_back", None)
                    st.rerun()

        st.markdown("<div style='margin-bottom: 0.75rem'></div>", unsafe_allow_html=True)

        _render_menu()
        _save_section()
        _local_downloads_tab()
        st.divider()
        _render_github_repo(
            repo_url="https://github.com/MIRO-UCLouvain/RT-Model-Card",
        )
        st.divider()
        st.link_button(
            "Open an Issue ↗",
            "https://github.com/MIRO-UCLouvain/RT-Model-Card/issues",
            use_container_width=True,
        )
