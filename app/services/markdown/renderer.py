"""Module to render the model card from session state to Markdown and PDF."""

from __future__ import annotations

import base64
import logging
import mimetypes
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

import markdown
import streamlit as st
from jinja2 import (
    Environment,
    FileSystemLoader,
    TemplateNotFound,
    select_autoescape,
)

from app.core.model_card.constants import DATA_INPUT_OUTPUT_TS
from app.core.templates.registry import (
    SECTION_REGISTRY,
    TEMPLATES_DIR,
)
from app.services.evaluations_extractor import (
    extract_evaluations_from_state,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

try:
    from weasyprint import CSS, HTML  # type: ignore[import-untyped]

    _HAS_WEASYPRINT: bool = True
    _WEASYPRINT_ERR: Exception | None = None
except (ImportError, OSError) as e:
    _HAS_WEASYPRINT = False
    _WEASYPRINT_ERR = e


@dataclass(frozen=True)
class FileObj:
    """Normalized representation for an uploaded file."""

    name: str | None
    type: str | None
    url: str | None


PREFIX_HW_SW = "hw_and_sw_"
PREFIX_CARD_META = "card_metadata_"
PREFIX_MODEL_BASIC = "model_basic_information_"
PREFIX_TECH_SPEC = "technical_specifications_"
PREFIX_TRAINING = "training_data_"
PREFIX_EVALS = "evaluations_"

_MARKDOWN_EXTENSIONS = [
    "tables",
    "fenced_code",
    "toc",
    "attr_list",
    "sane_lists",
]

_LOGGER = logging.getLogger(__name__)


def _safe_session_items() -> Iterable[tuple[str, Any]]:
    """
    Iterate over session_state items, only string keys.

    :return: An iterable of (key, value) pairs.
    :rtype: Iterable[tuple[str, Any]]
    :yield: (key, value) pairs from session_state.
    :rtype: Iterator[Iterable[tuple[str, Any]]]
    """
    for k, v in st.session_state.items():
        if isinstance(k, str):
            yield k, v


def build_appendix_files_context() -> list[dict[str, Any]]:
    """
    Build the context for rendering appendix files.

    :return: A list of dictionaries containing file metadata.
    :rtype: list[dict[str, Any]]
    """
    items: list[dict[str, Any]] = []
    uploads = getattr(st.session_state, "appendix_uploads", {}) or {}
    for original_name, data in uploads.items():
        stored_key = data.get("stored_name")
        norm = (
            _normalize_render_key_to_fileobj(stored_key)
            if stored_key
            else None
        )
        mime = (norm or {}).get("type")
        is_image = bool(mime and str(mime).lower().startswith("image/"))
        items.append(
            {
                "label": (data.get("custom_label") or "").strip(),
                "file": {
                    "name": original_name,
                    "key": stored_key,
                    "type": mime,
                    "url": (norm or {}).get("url"),
                    "is_image": is_image,
                },
            },
        )
    return items


def _format_date(
    raw: str | None,
    in_fmt: str = "%Y%m%d",
    out_fmt: str = "%Y/%m/%d",
) -> str | None:
    """
    Format date safely; return original on parse failure.

    :param raw: Raw date string to format.
    :type raw: str | None
    :param in_fmt: Input format string, defaults to "%Y%m%d"
    :type in_fmt: str, optional
    :param out_fmt: Output format string, defaults to "%Y/%m/%d"
    :type out_fmt: str, optional
    :return: Formatted date string or original on parse failure.
    :rtype: str | None
    """
    if not raw:
        return None
    try:
        dt = datetime.strptime(raw, in_fmt).replace(tzinfo=UTC)
        return dt.strftime(out_fmt)
    except (ValueError, TypeError):
        return raw


def _to_data_uri(mime: str | None, data: bytes) -> str | None:
    """
    Convert binary data to a data URI.

    :param mime: MIME type of the data.
    :type mime: str | None
    :param data: Binary data to encode.
    :type data: bytes
    :return: Data URI or None if encoding fails.
    :rtype: str | None
    """
    try:
        b64 = base64.b64encode(data).decode("ascii")
    except (TypeError, UnicodeDecodeError):
        return None
    else:
        return f"data:{mime or 'application/octet-stream'};base64,{b64}"


def _file_to_data_uri(
    path: str,
    fallback_mime: str | None = None,
) -> str | None:
    """
    Open local file and return data URI if it's an image.

    :param path: Path to the local file.
    :type path: str
    :param fallback_mime: Fallback MIME type if detection fails,
        defaults to None
    :type fallback_mime: str | None, optional
    :return: Data URI or None if file is not an image.
    :rtype: str | None
    """
    try:
        mime, _ = mimetypes.guess_type(path)
        mime = mime or fallback_mime
        if not mime or not mime.lower().startswith("image/"):
            return None
        with open(path, "rb") as f:  # noqa: PTH123
            data = f.read()
        return _to_data_uri(mime, data)
    except (OSError, TypeError, ValueError):
        return None


def _normalize_upload_entry(
    full_key: str,
    bucket: dict[str, Any],
) -> FileObj | None:
    """
    Normalize file info from a provided uploads bucket.

    :param full_key: Full key of the uploaded file.
    :type full_key: str
    :param bucket: Uploads bucket containing file info.
    :type bucket: dict[str, Any]
    :return: Normalized file object or None if not found.
    :rtype: FileObj | None
    """
    info = bucket.get(full_key)
    if not info:
        return None

    path = info.get("path")
    name = info.get("name") or (Path(path).name if path else None)

    mime, _ = mimetypes.guess_type(name or "")

    url = (
        _file_to_data_uri(path, fallback_mime=mime)
        if path and Path(path).exists()
        else None
    )

    return FileObj(name=name, type=mime, url=url)


def _normalize_file_from_key(
    full_key: str,
) -> dict[str, str | None] | None:
    """
    Normalize file object from session state.

    :param full_key: Full key of the uploaded file.
    :type full_key: str
    :return: Normalized file object or None if not found.
    :rtype: dict[str, str | None] | None
    """
    uploads: dict[str, Any] = st.session_state.get("render_uploads", {})
    norm = _normalize_upload_entry(full_key, uploads)
    return (
        None
        if norm is None
        else {
            "name": norm.name,
            "type": norm.type,
            "url": norm.url,
        }
    )


def _collect_hw_sw_from_state() -> dict[str, Any]:
    """
    Collect hardware/software info from session_state.

    :return: Hardware/software info.
    :rtype: dict[str, Any]
    """
    hw: dict[str, Any] = {}
    for key, val in _safe_session_items():
        if key.startswith(PREFIX_HW_SW):
            hw[key[len(PREFIX_HW_SW) :]] = val
    return hw


def _collect_learning_architectures_from_state() -> list[dict[str, Any]]:
    """
    Collect learning architectures from session_state.

    :return: List of learning architecture info.
    :rtype: list[dict[str, Any]]
    """
    grouped: dict[int, dict[str, Any]] = {}
    patterns = [
        re.compile(r"^learning_architecture_(\d+)_(.+)$"),
        re.compile(
            r"^technical_specifications_learning_architecture_(\d+)_(.+)$",
        ),
    ]

    for key, val in _safe_session_items():
        for pat in patterns:
            m = pat.match(key)
            if m:
                idx = int(m.group(1))
                field = m.group(2)
                grouped.setdefault(idx, {})[field] = val
                break

    forms = st.session_state.get("learning_architecture_forms") or {}
    for i in range(len(forms)):
        grouped.setdefault(i, {})

    result: list[dict[str, Any]] = []
    for i in sorted(grouped):
        la = grouped[i]
        la["id"] = i
        for k in (
            f"learning_architecture_{i}_architecture_figure",
            f"technical_specifications_learning_architecture_{i}_"
            "architecture_figure",
        ):
            norm = _normalize_file_from_key(k)
            if norm:
                la["architecture_figure"] = norm
                break
        result.append(la)
    return result


def _normalize_render_key_to_fileobj(
    full_key: str,
) -> dict[str, str | None] | None:
    """
    Normalize render key to file object.

    :param full_key: Full key of the uploaded file.
    :type full_key: str
    :return: Normalized file object or None if not found.
    :rtype: dict[str, str | None] | None
    """
    uploads: dict[str, Any] = st.session_state.get("render_uploads", {})
    norm = _normalize_upload_entry(full_key, uploads)
    return (
        None
        if norm is None
        else {
            "name": norm.name,
            "type": norm.type,
            "url": norm.url,
        }
    )


def _prime_normalized_uploads() -> None:
    """Normalize uploaded files and cache in session_state."""
    uploads: dict[str, Any] = st.session_state.get("render_uploads", {})
    norm: dict[str, dict[str, str | None]] = {}
    for key in list(uploads):
        try:
            obj = _normalize_render_key_to_fileobj(key)
        except (OSError, FileNotFoundError, ValueError, TypeError):
            _LOGGER.exception("Failed to normalize upload %r", key)
            continue
        if obj:
            norm[key] = obj
    st.session_state["normalized_uploads"] = norm


def build_context_for_prefix(prefix: str) -> dict[str, Any]:  # noqa: C901, PLR0912, PLR0915
    """
    Build a context dictionary for a specific prefix.

    :param prefix: The prefix to filter session items.
    :type prefix: str
    :return: A dictionary containing the filtered session items.
    :rtype: dict[str, Any]
    """
    ctx: dict[str, Any] = {}
    try:
        if isinstance(prefix, str):
            ctx.update(
                {
                    k: v
                    for k, v in _safe_session_items()
                    if k.startswith(prefix)
                },
            )
        if prefix == PREFIX_CARD_META:
            if "card_metadata_card_creation_date" in ctx:
                ctx["card_metadata_card_creation_date"] = _format_date(
                    ctx.get("card_metadata_card_creation_date"),
                )
            ctx["model_basic_information_name"] = st.session_state.get(
                "model_basic_information_name",
                "",
            )
            ctx["task"] = st.session_state.get("task", "")
        if (
            prefix == PREFIX_MODEL_BASIC
            and "model_basic_information_creation_date" in ctx
        ):
            ctx["model_basic_information_creation_date"] = _format_date(
                ctx.get("model_basic_information_creation_date"),
            )
        if prefix == PREFIX_TECH_SPEC:
            ctx["learning_architectures"] = (
                _collect_learning_architectures_from_state()
            )
            hw = _collect_hw_sw_from_state()
            if hw:
                ctx["hw_and_sw"] = hw
            for k in ["technical_specifications_model_pipeline_figure"]:
                norm = _normalize_file_from_key(k)
                if norm:
                    ctx[k] = norm
            for i, la in enumerate(ctx.get("learning_architectures", [])):
                la_key1 = f"learning_architecture_{i}_architecture_figure"
                la_key2 = (
                    "technical_specifications_learning_architecture_"
                    f"{i}_architecture_figure"
                )
                norm = _normalize_file_from_key(
                    la_key1,
                ) or _normalize_file_from_key(la_key2)
                if norm:
                    la["architecture_figure"] = norm
        if prefix == PREFIX_TRAINING:
            ctx["DATA_INPUT_OUTPUT_TS"] = DATA_INPUT_OUTPUT_TS
            modality_entries: list[dict[str, str]] = []
            for key, value in _safe_session_items():
                if key.endswith("model_inputs") and isinstance(value, list):
                    modality_entries.extend(
                        {"modality": item, "source": "model_inputs"}
                        for item in value
                    )
                elif key.endswith("model_outputs") and isinstance(value, list):
                    modality_entries.extend(
                        {"modality": item, "source": "model_outputs"}
                        for item in value
                    )
            io_details: list[dict[str, Any]] = []
            for entry in modality_entries:
                clean = entry["modality"].strip().replace(" ", "_").lower()
                source = entry["source"]
                detail: dict[str, Any] = {
                    "entry": entry["modality"],
                    "source": source,
                }
                for field_key in DATA_INPUT_OUTPUT_TS:
                    per_mod_key = f"training_data_{clean}_{source}_{field_key}"
                    val = (
                        st.session_state.get(per_mod_key)
                        or st.session_state.get(f"_{per_mod_key}")
                        or st.session_state.get(f"__{per_mod_key}")
                        or ""
                    )
                    if not val:
                        global_key = f"training_data_{field_key}"
                        val = st.session_state.get(global_key, "")
                    detail[field_key] = val
                io_details.append(detail)
            ctx["training_data_inputs_outputs_technical_specifications"] = (
                io_details
            )
        if prefix == PREFIX_EVALS:
            _prime_normalized_uploads()
            ev = extract_evaluations_from_state()
            ctx["evaluations"] = ev if isinstance(ev, list) else []
            for e in ctx["evaluations"]:
                if "evaluation_date" in e:
                    e["evaluation_date"] = _format_date(
                        e.get("evaluation_date"),
                    )
            task_val = st.session_state.get("task", "")
            ctx["task"] = task_val
            try:
                from app.core.model_card.constants import (  # noqa: PLC0415
                    TASK_METRIC_MAP,
                )

                task_key = (task_val or "").strip()
                ctx["metric_groups"] = TASK_METRIC_MAP.get(task_key, [])
            except (ImportError, AttributeError):
                ctx["metric_groups"] = []
            ctx["normalized_uploads"] = st.session_state.get(
                "normalized_uploads",
                {},
            )
    except (
        KeyError,
        TypeError,
        AttributeError,
        OSError,
        ValueError,
    ):
        pass
    return ctx


@lru_cache(maxsize=1)
def _env() -> Environment:
    """
    Construct (and cache) the Jinja2 environment.

    :return: Jinja2 environment instance.
    :rtype: Environment
    """
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(
            enabled_extensions=(),
            default_for_string=False,
        ),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["DATA_INPUT_OUTPUT_TS"] = DATA_INPUT_OUTPUT_TS
    env.globals["FIG_FIELD"] = {
        "type_ism": "figure_ism",
        "type_dose_dm": "figure_dm",
        "type_gm_seg": "figure_gm_seg",
        "type_dose_dm_seg": "figure_dm_seg",
        "type_dose_dm_dp": "figure_dm_dp",
        "type_metrics_other": "figure_other",
    }
    return env


def render_section_md(section_id: str) -> str:
    """
    Render a section of the model card markdown.

    :param section_id: ID of the section to render.
    :type section_id: str
    :raises FileNotFoundError: If the template file is not found.
    :return: Rendered markdown for the section.
    :rtype: str
    """
    cfg = SECTION_REGISTRY[section_id]
    ctx = build_context_for_prefix(cfg["prefix"])
    if not isinstance(ctx, dict):
        ctx = {}
    try:
        return _env().get_template(cfg["template"]).render(**ctx)
    except TemplateNotFound as exc:
        msg = f"Template not found: {cfg['template']}"
        raise FileNotFoundError(msg) from exc


def render_full_model_card_md(
    master_template: str = "model_card_master.md.j2",
) -> str:
    """
    Render the full model card markdown.

    :param master_template: Path to the master template file,
        defaults to "model_card_master.md.j2"
    :type master_template: str, optional
    :return: Rendered markdown for the full model card.
    :rtype: str
    """
    sections_md = {sid: render_section_md(sid) for sid in SECTION_REGISTRY}
    appendix_files = build_appendix_files_context()
    return (
        _env()
        .get_template(master_template)
        .render(
            sections=sections_md,
            appendix_files=appendix_files,
        )
    )

DEFAULT_PDF_CSS = """
/* --- Page setup --- */
@page {
  size: A4;
  margin: 18mm 14mm 20mm 14mm;
  @bottom-center {
    content: "Page " counter(page) " of " counter(pages);
    font-size: 8.6px;
    color: #6b7280;
  }
}

/* --- Palette --- */
:root{
  --brand: #0553D1;   /* main color */
  --accent: #05B9D1;  /* secondary color */
  --text: #111111;    /* negro para títulos y texto principal */
  --muted: #4b5563;
  --muted-2: #6b7280;
  --border: #e5e7eb;
  --bg-soft: #f8fafc;
  --bg-soft-2: #f3f4f6;
  --table-head: #05B9D1;
}

/* --- Base text (-0.4pt) --- */
html, body {
  font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
  Arial, "Noto Sans", sans-serif;
  font-size: 9.6pt;
  line-height: 1.5;
  color: var(--text);
}
p, li { hyphens: auto; margin: 0.35em 0 0.6em; }

/* --- H1 --- */
h1 {
  font-size: 15.6pt;
  font-weight: 700;
  color: var(--text);  /* negro */
  margin: 1em 0 0.6em;
  string-set: section content();
}

/* --- H2 --- */
h2 {
  font-size: 13.6pt;
  font-weight: 700;
  color: #fff;
  background: var(--brand);  /* main color */
  border-radius: 4px;
  padding: 6px 10px;
  margin: 0.9em 0 0.55em;
  string-set: section content();
}

/* --- H3 --- */
h3 {
  font-size: 12.1pt;
  font-weight: 600;
  color: var(--text);  /* negro */
}

/* --- H4 --- */
h4 {
  font-size: 10.9pt;
  font-weight: 600;
  color: #374151; /* gris oscuro */
}

h5 {
  font-size: 10.1pt;
  font-weight: 600;
  color: var(--muted-2);
}

/* --- Lists --- */
ul {
  margin: 0.3em 0 0.7em 1.2em;
  list-style: none;
  padding-left: 0;
}
ul li {
  margin: 0.2em 0;
  padding-left: 1em;
  position: relative;
}
ul li::before {
  content: "–";
  position: absolute;
  left: 0;
  color: var(--brand); /* main color */
  font-weight: 600;
}

/* --- Tables --- */
table {
  border-collapse: collapse;
  width: 100%;
  margin: 0.5em 0 1em;
  table-layout: fixed;
  font-size: 9.8pt;
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
}

caption {
  caption-side: top;
  text-align: left;
  font-weight: 700;
  color: var(--text); /* negro */
  padding: 6px 0;
}

thead th {
  background: var(--table-head);
  color: #fff;
  font-weight: 600;
  text-align: left;
}

th, td {
  border: 1px solid var(--border);
  padding: 6px 8px;
  vertical-align: top;
  word-wrap: break-word;
}

tbody tr:nth-child(even) td {
  background: #f9fafb;
}

tbody tr:hover td {
  background: #f3f6fb; /* hover suave (solo digital) */
}

.badge {
  display: inline-block;
  font-size: 8.8pt;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--accent); /* secondary color */
  color: var(--brand);       /* main color */
}

/* --- Figures --- */
figure {
  margin: 0.7em auto 1em;
  text-align: center;
  page-break-inside: avoid;
}
img, figure img {
  display: block;
  max-width: 70%;
  height: auto;
  margin: 0.4em auto;
  border: 1px solid var(--border);
  border-radius: 6px;
}
figcaption { font-size: 9pt; color: var(--muted); margin-top: 0.3em; }
"""



def render_markdown_to_html(
    md_text: str,
    extra_css: str | None = None,
) -> str:
    """
    Render the given Markdown text to HTML.

    :param md_text: The Markdown text to render.
    :type md_text: str
    :param extra_css: Additional CSS styles to include, defaults to None
    :type extra_css: str | None, optional
    :return: The rendered HTML.
    :rtype: str
    """
    html_body = markdown.markdown(
        md_text,
        extensions=_MARKDOWN_EXTENSIONS,
        output_format="html",
    )
    css_block = f"<style>{DEFAULT_PDF_CSS}</style>"
    if extra_css:
        css_block += f"<style>{extra_css}</style>"
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Model Card</title>
{css_block}
</head>
<body>
{html_body}
</body>
</html>"""


def save_model_card_pdf(
    path: str = "model_card.pdf",
    *,
    css_text: str = DEFAULT_PDF_CSS,
    css_file: str | None = None,
    base_url: str | None = None,
) -> str:
    """
    Save the model card as a PDF file.

    :param path: The file path to save the PDF, defaults to "model_card.pdf"
    :type path: str, optional
    :param css_text: Additional CSS styles to include, defaults to
        DEFAULT_PDF_CSS
    :type css_text: str, optional
    :param css_file: The file path to a CSS file to include, defaults to None
    :type css_file: str | None, optional
    :param base_url: The base URL for resolving relative paths,
        defaults to None
    :type base_url: str | None, optional
    :raises RuntimeError: If WeasyPrint is not installed or missing
        system libraries
    :return: The file path to the saved PDF
    :rtype: str
    """
    if not _HAS_WEASYPRINT:
        msg = (
            "PDF export unavailable: WeasyPrint not installed or "
            "missing system libraries.\n"
            f"Underlying error: {_WEASYPRINT_ERR}"
        )
        raise RuntimeError(msg)

    md = render_full_model_card_md()
    html = render_markdown_to_html(md, extra_css=css_text)

    css_list = []
    if css_file:
        css_list.append(CSS(filename=css_file))
    if css_text:
        css_list.append(CSS(string=css_text))

    HTML(string=html, base_url=base_url).write_pdf(path, stylesheets=css_list)
    return path


__all__ = [
    # constants
    "DEFAULT_PDF_CSS",
    "_HAS_WEASYPRINT",
    "_WEASYPRINT_ERR",
    "_collect_hw_sw_from_state",
    "_collect_learning_architectures_from_state",
    "_env",
    "_file_to_data_uri",
    # private (kept exported to avoid breaking imports relying on star)
    "_format_date",
    "_normalize_file_from_key",
    "_normalize_render_key_to_fileobj",
    "_prime_normalized_uploads",
    "_to_data_uri",
    # public API
    "build_appendix_files_context",
    "build_context_for_prefix",
    "render_full_model_card_md",
    "render_markdown_to_html",
    "render_section_md",
    "save_model_card_pdf",
]
