"""Module to build the YAML front matter for a model card."""

from __future__ import annotations

import logging
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

from app.services.markdown.renderer import render_full_model_card_md

if TYPE_CHECKING:
    from collections.abc import Iterable

# logger to capture exceptions
logger = logging.getLogger(__name__)

# Minimal YAML front matter builder (no external deps)
Scalar = Union[str, int, float, bool]
YAMLish = Union[Scalar, list[Scalar], dict[str, Any]]


def _is_nonempty(x: object) -> bool:
    if x is None:
        return False
    if isinstance(x, str):
        return x.strip() != ""
    if isinstance(x, (list, dict, tuple, set)):
        return len(x) > 0
    return True


def _yaml_escape_scalar(v: Scalar) -> str:
    """
    Conservative quoting to avoid YAML pitfalls without a parser.

    :param v: The scalar value to quote.
    :type v: Scalar
    :return: The quoted scalar value.
    :rtype: str
    """
    if isinstance(v, bool):
        return "true" if v else "false"
    s = str(v)
    needs_quote = (
        s.strip() != s
        or s == ""
        or any(
            s.lower() == t for t in ["null", "~", "true", "false", "yes", "no"]
        )
        or s[0] in "-?:@{}[],&*!#|>%'\"`"
        or any(ch in s for ch in [":", "#"])
    )
    if needs_quote:
        s = s.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{s}"'
    return s


def _emit_yaml_lines(key: str, value: YAMLish, indent: int = 0) -> list[str]:
    """Emit simple YAML for scalars, lists, and flat dicts."""
    sp = " " * indent
    out: list[str] = []

    if isinstance(value, dict):
        items = [(k, v) for k, v in value.items() if _is_nonempty(v)]
        if not items:
            return out
        out.append(f"{sp}{key}:")
        for k, v in items:
            out.extend(_emit_yaml_lines(str(k), v, indent + 2))
        return out

    if isinstance(value, (list, tuple, set)):
        seq: list[Any] = [v for v in value if _is_nonempty(v)]
        if not seq:
            return out
        out.append(f"{sp}{key}:")
        for v in seq:
            if isinstance(v, (list, dict)):
                out.append(f"{sp}  -")
                if isinstance(v, dict):
                    for k2, v2 in v.items():
                        if _is_nonempty(v2):
                            out.extend(
                                _emit_yaml_lines(
                                    str(k2),
                                    v2,
                                    indent + 4,
                                ),
                            )
                else:
                    for i2, v2 in enumerate(v):
                        out.extend(
                            _emit_yaml_lines(
                                str(i2),
                                v2,
                                indent + 4,
                            ),
                        )
            else:
                out.append(f"{sp}  - {_yaml_escape_scalar(v)}")
        return out

    out.append(f"{sp}{key}: {_yaml_escape_scalar(value)}")
    return out


def _build_front_matter(meta: dict[str, Any]) -> str:
    # Remove empties + keep insertion order
    compact = {k: v for k, v in meta.items() if _is_nonempty(v)}
    lines: list[str] = ["---"]
    for k, v in compact.items():
        lines.extend(_emit_yaml_lines(k, v))
    lines.append("---\n")
    return "\n".join(lines)


HF_META_KEYS: set[str] = {
    "pipeline_tag",
    "library_name",
    "license",
    "license_name",
    "license_link",
    "language",
    "tags",
    "thumbnail",
    "datasets",
    "metrics",
    "base_model",
    "base_models",
    "new_version",
    "model-index",
}


def _norm_list(v: object) -> list[str]:
    if isinstance(v, str):
        parts = [p.strip() for p in v.split(",")]
        return [p for p in parts if p]
    if isinstance(v, (list, tuple, set)):
        return [str(x) for x in v if _is_nonempty(x)]
    return []


def _extract_metrics_from_evaluations(ss: dict[str, Any]) -> list[str]:
    """Return a flat list of metric identifiers from evaluations."""
    metrics: list[str] = []
    evals: Iterable[Any] = ss.get("evaluations") or []
    for e in evals:
        if not isinstance(e, dict):
            continue
        name = e.get("metric_name") or e.get("metric")
        if name:
            metrics.append(str(name))
        inner = e.get("metrics") or []
        norm_inner = inner if isinstance(inner, list) else _norm_list(inner)
        for m in norm_inner:
            if isinstance(m, dict):
                mname = m.get("name") or m.get("type")
                if mname:
                    metrics.append(str(mname))
            elif isinstance(m, str):
                metrics.append(m)
    seen: set[str] = set()
    out: list[str] = []
    for m in metrics:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def _extract_base_model_from_training_data(
    ss: dict[str, Any],
) -> str | list[str] | None:
    """Pull base model from training data (single string or list)."""
    td = ss.get("training_data") or {}
    base = (
        td.get("model_name") or ss.get("base_model") or ss.get("base_models")
    )
    if not base:
        return None
    if isinstance(base, (list, tuple, set)):
        return [str(x) for x in base if _is_nonempty(x)]
    return str(base)


def _collect_hf_meta_from_session_state() -> dict[str, YAMLish]:
    """Collect specific fields from Streamlit session_state."""
    try:
        import streamlit as st  # noqa: PLC0415
    except ImportError:
        # Streamlit no disponible (p.ej., ejecución offline)
        return {}

    ss: dict[str, Any] = getattr(st, "session_state", {}) or {}

    pipeline_tag: str | None = ss.get("pipeline_tag") or ss.get("task") or ""
    if isinstance(pipeline_tag, str):
        pipeline_tag = pipeline_tag.strip().lower().replace(" ", "-") or None

    libs = _norm_list(
        ss.get("libraries")
        or ss.get("dependencies")
        or ss.get("library_name"),
    )
    library_name: str | None = libs[0] if libs else None
    extra_lib_tags: list[str] = libs[1:] if len(libs) > 1 else []

    license_val: Any = ss.get("license") or ss.get(
        "model_basic_information_software_license",
    )

    language = ["en"]

    tags: list[str] = _norm_list(ss.get("tags")) + extra_lib_tags

    datasets = _norm_list(
        ss.get("datasets") or (ss.get("training_data") or {}).get("datasets"),
    )

    metrics = _extract_metrics_from_evaluations(ss)
    base_model = _extract_base_model_from_training_data(ss)

    thumbnail: Any = ss.get("thumbnail")
    new_version: Any = ss.get("new_version")

    meta: dict[str, Any] = {
        "pipeline_tag": pipeline_tag,
        "library_name": library_name,
        "license": license_val,
        "language": language,
        "tags": tags,
        "thumbnail": thumbnail,
        "datasets": datasets,
        "metrics": metrics,
        "base_model": base_model,
        "new_version": new_version,
    }

    mi = ss.get("model-index") or ss.get("model_index")
    if _is_nonempty(mi):
        meta["model-index"] = mi

    return {k: v for k, v in meta.items() if _is_nonempty(v)}


def render_hf_readme(
    *,
    meta: dict[str, YAMLish] | None = None,
    master_template: str = "model_card_master.md.j2",
) -> str:
    """Return a complete Hugging Face README.md string."""
    session_meta = _collect_hf_meta_from_session_state()
    merged_meta: dict[str, Any] = {}
    for k in HF_META_KEYS:
        if meta and k in meta and _is_nonempty(meta[k]):
            merged_meta[k] = meta[k]
        elif k in session_meta:
            merged_meta[k] = session_meta[k]

    if "base_models" in merged_meta and "base_model" not in merged_meta:
        merged_meta["base_model"] = merged_meta.pop("base_models")

    body_md = render_full_model_card_md(master_template=master_template)

    fm = _build_front_matter(merged_meta)
    return f"{fm}{body_md}"


def save_hf_readme(
    path: str = "README.md",
    *,
    meta: dict[str, YAMLish] | None = None,
    master_template: str = "model_card_master.md.j2",
) -> str:
    """Render and write the HF model card README.md to `path`."""
    content = render_hf_readme(
        meta=meta,
        master_template=master_template,
    )
    with Path(path).open("w", encoding="utf-8") as f:
        f.write(content)
    return path


def upload_readme_to_hub(
    repo_id: str,
    *,
    token: str | None = None,
    readme_path: str = "README.md",
    create_if_missing: bool = True,
) -> None:
    """Upload README.md to a model repo on the Hugging Face Hub."""
    try:
        from huggingface_hub import (  # noqa: PLC0415
            HfApi,
            create_repo,
        )
    except ImportError as exc:  # pragma: no cover
        msg = (
            "huggingface_hub is required. Install with "
            "`pip install huggingface_hub`."
        )
        raise RuntimeError(msg) from exc

    api = HfApi(token=token)

    if create_if_missing:
        # Ignora silenciosamente errores al crear el repo (existente, perms)
        with suppress(Exception):
            create_repo(
                repo_id=repo_id,
                token=token,
                repo_type="model",
                exist_ok=True,
            )

    api.upload_file(
        path_or_fileobj=readme_path,
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type="model",
    )


def build_model_index_from_evaluations(
    model_name: str,
) -> dict[str, Any] | None:
    """Convert evaluations into HF model-index (best effort)."""
    try:
        from app.services.evaluations_extractor import (  # noqa: PLC0415
            extract_evaluations_from_state,
        )
    except ImportError:
        return None

    evals = extract_evaluations_from_state() or []
    results: list[dict[str, Any]] = []
    for e in evals:
        if not isinstance(e, dict):
            continue
        try:
            task_raw = e.get("task") or "text-generation"
            task_type = str(task_raw).strip()
            ds_name = e.get("dataset_name") or e.get("dataset")
            ds_type = e.get("dataset_id") or ds_name
            metric_name = e.get("metric_name") or e.get("metric")
            metric_value = e.get("metric_value") or e.get("value")
            valid = ds_name and metric_name and metric_value is not None
            if not valid:
                continue
            results.append(
                {
                    "task": {"type": task_type},
                    "dataset": {"name": ds_name, "type": ds_type},
                    "metrics": [
                        {
                            "name": metric_name,
                            "type": metric_name,
                            "value": metric_value,
                        },
                    ],
                },
            )
        except Exception:  # mantener el comportamiento: continuar
            logger.exception(
                "Skipping evaluation entry due to parsing error.",
            )
            continue

    if not results:
        return None

    return {"model-index": [{"name": model_name, "results": results}]}
