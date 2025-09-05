"""Module Sidebar of the Model Card UI (refactored, same functionality)."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Any

import streamlit as st

from app.core.model_card.constants import SCHEMA
from app.services.markdown.renderer import render_full_model_card_md
from app.services.readme.builder import (
    render_hf_readme,
    upload_readme_to_hub,
)
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
from app.ui.utils.typography import enlarge_tab_titles

model_card_schema: dict[str, Any] = get_model_card_schema()

st.set_page_config(layout="wide", initial_sidebar_state="expanded")

SIDEBAR_WIDTH_PX: int = 500
REPO_ID_PARTS: int = 2

# Location of the external CSS file
CSS_PATH = (Path(__file__).resolve().parent.parent / "static" / "sidebar.css")
# Navigation helpers


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
        "Training Data Methodology and Information",
        use_container_width=True,
    ):
        st.session_state.runpage = training_data_render
        st.rerun()

    if st.button(
        "Evaluation Data Methodology, Results and Commissioning",
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


# Download helpers (Local tab)


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
                with zipfile.ZipFile(
                    buffer,
                    "w",
                    compression=zipfile.ZIP_DEFLATED,
                ) as zf:
                    for fpath in valid_files:
                        arcname = Path(fpath).name
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
                with zipfile.ZipFile(
                    buffer,
                    "w",
                    compression=zipfile.ZIP_DEFLATED,
                ) as zf:
                    zf.writestr("model_card.json", card_content)
                    for fpath in valid_files_zip:
                        arcname = f"files/{Path(fpath).name}"
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


# README tab helpers


def _readme_generate_form() -> None:
    with st.form("form_generate_readme"):
        if st.form_submit_button("Generate README.md"):
            try:
                _ = parse_into_json(SCHEMA)
                generated = render_hf_readme()
                st.session_state.last_readme_text = generated
                st.success(
                    "README built successfully. Use the download button "
                    "below.",
                )
            except (
                ValueError,
                RuntimeError,
                OSError,
                TypeError,
            ) as e:
                st.session_state.last_readme_text = None
                st.error(f"Could not build README: {e}")


def _readme_download_preview() -> None:
    if not st.session_state.last_readme_text:
        return
    st.download_button(
        "Download README.md",
        data=st.session_state.last_readme_text.encode("utf-8"),
        file_name="README.md",
        mime="text/markdown",
        use_container_width=True,
        key="btn_download_readme",
    )
    with st.expander("Preview README.md", expanded=False):
        st.text_area(
            "README.md",
            value=st.session_state.last_readme_text,
            height=300,
            key="ta_readme_preview",
        )


def _hub_push_form() -> None:
    st.markdown("## Export README.md to Hub")
    with st.form("form_upload_readme_hub"):
        st.markdown(
            "Use a token with write access from "
            "[here](https://hf.co/settings/tokens)",
        )
        token_rm = st.text_input(
            "Token",
            type="password",
            key="token_rm_hub",
        )
        repo_id_rm = st.text_input(
            "Repo ID (e.g. user/repo)",
            key="repo_id_rm_hub",
        )
        push_rm = st.form_submit_button("Upload README.md to Hub")

    if not push_rm:
        return
    if len(repo_id_rm.split("/")) != REPO_ID_PARTS:
        st.error(
            "Repo ID invalid. It should be username/repo-name. For "
            "example: nateraw/food",
        )
        return
    try:
        if not st.session_state.get("last_readme_text"):
            st.session_state.last_readme_text = render_hf_readme()
        tmp_path = "README.md"
        with open(tmp_path, "w", encoding="utf-8") as f:  # noqa: PTH123
            f.write(st.session_state.last_readme_text)
        upload_readme_to_hub(
            repo_id=repo_id_rm,
            token=token_rm or None,
            readme_path=tmp_path,
            create_if_missing=True,
        )
        new_url = f"https://huggingface.co/{repo_id_rm}"
        st.success(
            f"Pushed the README to the repo [here]({new_url})!",
        )
    except (OSError, RuntimeError, ValueError) as e:
        st.error(f"Error: {e!s}")


def _readme_tab() -> None:
    task = st.session_state.get("task", "Image-to-Image translation")
    _ = validate_required_fields(model_card_schema, current_task=task)
    if "last_readme_text" not in st.session_state:
        st.session_state.last_readme_text = None
    _readme_generate_form()
    _readme_download_preview()
    _hub_push_form()


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


def sidebar_render() -> None:
    """Render the sidebar for the Streamlit app."""
    with st.sidebar:
        inject_css(CSS_PATH)
        _render_menu()
        st.markdown("## Model Card Builder")
        enlarge_tab_titles(16)
        tab_local, tab_readme = st.tabs(
            ["Local downloads", "Upload README to Hub"],
        )
        with tab_local:
            _local_downloads_tab()
        with tab_readme:
            _readme_tab()
        st.divider()
        _render_github_repo(
            repo_url="https://github.com/MIRO-UCLouvain/RT-Model-Card",
        )
