"""Module to validate required fields in the model card schema."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import streamlit as st

from app.core.model_card.constants import (
    DATA_INPUT_OUTPUT_TS,
    EVALUATION_METRIC_FIELDS,
    LEARNING_ARCHITECTURE,
    TASK_METRIC_MAP,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

MissingItem = tuple[str, str]  # (section, human_readable_label)
_EMPTY_SENTINELS: tuple[Any, ...] = ("", None, [], {})

_METRIC_SUFFIX_RE = re.compile(r"(?: \d+)$")


def _metric_base_name(name: str) -> str:
    """
    Remove trailing ' #n' suffix from a metric label.

    :param name: The metric label.
    :type name: str
    :return: The base name of the metric.
    :rtype: str
    """
    return _METRIC_SUFFIX_RE.sub("", str(name or ""))


def is_empty(value: object) -> bool:
    """
    Check if a value is considered empty for validation purposes.

    :param value: The value to check.
    :type value: object
    :return: True if the value is empty, otherwise False.
    :rtype: bool
    """
    return value in _EMPTY_SENTINELS


def _has_required_image(full_key: str) -> bool:
    """
    Check if the uploader for `full_key` has a saved image file on disk.

    :param full_key: The full key of the uploader.
    :type full_key: str
    :return: True if the image file exists, otherwise False.
    :rtype: bool
    """
    rec = st.session_state.get("render_uploads", {}).get(full_key)
    if not rec:
        return False
    try:
        return Path(rec.get("path", "")).exists()
    except (TypeError, OSError):
        return False


def _label_for(props: dict[str, Any], key: str) -> str:
    """
    Get a human-readable label by replacing underscores with spaces for a field key.

    :param props: The field properties.
    :type props: dict[str, Any]
    :param key: The field key.
    :type key: str
    :return: A human-readable label for the field key.
    :rtype: str
    """  # noqa: E501
    return (props.get("label") or key).replace("_", " ").title()


def _field_required_for_task(
    props: dict[str, Any],
    current_task: str | None,
) -> bool:
    """
    Check if a field is required for the current task context.

    :param props: The field properties.
    :type props: dict[str, Any]
    :param current_task: The current task identifier.
    :type current_task: str | None
    :return: True if the field is required for the current task context,
        otherwise False.
    :rtype: bool
    """
    if not props.get("required", False):
        return False
    allowed = props.get("model_types")
    # Ensure a boolean is always returned
    # (guards against empty-string current_task)
    return bool(allowed is None or (current_task and current_task in allowed))


def _modalities_from_state() -> list[tuple[str, str]]:
    """
    Extract (modality, source) pairs from session state.

    :return: A list of (modality, source) pairs.
    :rtype: list[tuple[str, str]]
    """
    modalities: list[tuple[str, str]] = []
    for key, value in st.session_state.items():
        if not isinstance(key, str) or not isinstance(value, list):
            continue
        if key.endswith("model_inputs"):
            modalities.extend((item, "model_inputs") for item in value)
        elif key.endswith("model_outputs"):
            modalities.extend((item, "model_outputs") for item in value)
    return modalities


def validate_static_fields(
    schema: dict[str, dict[str, dict[str, Any]]],
    current_task: str | None,
) -> list[MissingItem]:
    """
    Validate static fields in the model card schema.

    :param schema: The model card schema.
    :type schema: dict[str, dict[str, dict[str, Any]]]
    :param current_task: The current task identifier.
    :type current_task: str | None
    :return: A list of missing items.
    :rtype: list[MissingItem]
    """
    missing: list[MissingItem] = []

    skip_fields = set(DATA_INPUT_OUTPUT_TS.keys())
    skip_keys = {
        "input_content_rtstruct_subtype",
        "output_content_rtstruct_subtype",
    }
    skip_sections = {
        "evaluation_data_methodology_results_commisioning",
        "learning_architecture",
        "qualitative_evaluation",
    }

    for section, fields in schema.items():
        if section in skip_sections or not isinstance(fields, dict):
            continue
        for key, props in fields.items():
            if key in skip_keys or (
                key in skip_fields
                and section
                in [
                    "training_data",
                    "evaluation_data_methodology_results_commisioning",
                ]
            ):
                continue
            if not _field_required_for_task(props, current_task):
                continue

            full_key = f"{section}_{key}"
            ftype = (props.get("type") or "").lower()
            if ftype == "image":
                if not _has_required_image(full_key):
                    missing.append((section, _label_for(props, key)))
                continue

            if is_empty(st.session_state.get(full_key)):
                missing.append((section, _label_for(props, key)))
    return missing


def validate_learning_architectures(
    schema: dict[str, dict[str, dict[str, Any]]],
) -> list[MissingItem]:
    """
    Validate the repeated 'learning architecture' blocks.

    :param schema: The model card schema.
    :type schema: dict[str, dict[str, dict[str, Any]]]
    :return: A list of missing items.
    :rtype: list[MissingItem]
    """
    missing: list[MissingItem] = []
    forms = st.session_state.get("learning_architecture_forms", {})
    schema_fields = schema.get("learning_architecture", {})

    for i in range(len(forms)):
        prefix = f"learning_architecture_{i}_"
        for field in LEARNING_ARCHITECTURE:
            props = schema_fields.get(field)
            if not props or not props.get("required", False):
                continue
            if is_empty(st.session_state.get(f"{prefix}{field}")):
                label = props.get("label", field.replace("_", " ").title())
                missing.append(
                    (
                        "learning_architecture",
                        f"{label} (Learning Architecture {i + 1})",
                    ),
                )
    return missing


def validate_modalities_fields() -> list[MissingItem]:
    """
    Validate the fields for each modality in the model card.

    :return: A list of missing items.
    :rtype: list[MissingItem]
    """
    missing: list[MissingItem] = []
    modalities = _modalities_from_state()

    counts_train: dict[tuple[str, str], int] = {}
    for modality, source in modalities:
        clean = modality.strip().replace(" ", "_").lower()
        pair = (clean, source)
        idx = counts_train.get(pair, 0)
        counts_train[pair] = idx + 1

        prefix_train = f"training_data_{clean}_{source}_{idx}_"
        for field, label in DATA_INPUT_OUTPUT_TS.items():
            full = f"{prefix_train}{field}"
            if is_empty(st.session_state.get(full)):
                missing.append(
                    (
                        "training_data",
                        f"{label} ({modality} - {source})",
                    ),
                )

    for name in st.session_state.get("evaluation_forms", []):
        slug = name.replace(" ", "_")

        if st.session_state.get(f"evaluation_{slug}_ts_same_as_training"):
            continue

        counts_eval: dict[tuple[str, str], int] = {}
        for modality, source in modalities:
            clean = modality.strip().replace(" ", "_").lower()
            pair = (clean, source)
            idx = counts_eval.get(pair, 0)
            counts_eval[pair] = idx + 1

            for field, label in DATA_INPUT_OUTPUT_TS.items():
                full = (
                    f"evaluation_{slug}_{clean}_{source}_{idx}_{field}"
                )
                if is_empty(st.session_state.get(full)):
                    missing.append(
                        (
                            "evaluation_data_methodology_results_commisioning",
                            f"{label} ({modality} - {source})(Eval: {name})",
                        ),
                    )

    return missing



def _validate_metric_group(
    prefix: str,
    slug: str,
    name: str,
    metric_type: str,
    eval_section: dict[str, dict[str, Any]],
    missing: list[MissingItem],
) -> None:
    """
    Validate required fields inside one metric group by checking the evaluation section schema.

    :param prefix: The prefix for the metric fields.
    :type prefix: str
    :param slug: The slugified name of the evaluation form.
    :type slug: str
    :param name: The name of the evaluation form.
    :type name: str
    :param metric_type: The type of the metric.
    :type metric_type: str
    :param eval_section: The evaluation section schema.
    :type eval_section: dict[str, dict[str, Any]]
    :param missing: A list to collect missing items.
    :type missing: list[MissingItem]
    """  # noqa: E501
    entry_list: Sequence[str] = st.session_state.get(
        f"{prefix}{metric_type}_list",
        [],
    )
    for metric_id in entry_list:
        metric_prefix = f"evaluation_{slug}.{metric_id}"
        base = _metric_base_name(metric_id)
        short = base.split(" (")[0]
        for field_key in EVALUATION_METRIC_FIELDS.get(metric_type, []):
            props = eval_section.get(field_key)
            if props and props.get("required", False):
                full = f"{metric_prefix}_{field_key}"
                if is_empty(st.session_state.get(full)):
                    missing.append(
                        (
                            "evaluation_data_methodology_results_commisioning",
                            f"{_label_for(props, field_key)} "
                            f"(Metric: {short}, Eval: {name})",
                        ),
                    )



def validate_evaluation_forms(
    schema: dict[str, dict[str, dict[str, Any]]],
    current_task: str | None,
) -> list[MissingItem]:
    """
    Validate required fields for each evaluation form.

    :param schema: The model card schema.
    :type schema: dict[str, dict[str, dict[str, Any]]]
    :param current_task: The current task identifier.
    :type current_task: str | None
    :return: A list of missing items.
    :rtype: list[MissingItem]
    """
    missing: list[MissingItem] = []
    skip_fields = set(DATA_INPUT_OUTPUT_TS.keys())
    eval_section = schema.get(
        "evaluation_data_methodology_results_commisioning",
        {},
    )
    metric_types = TASK_METRIC_MAP.get(current_task or "", [])
    metric_keys = {
        f for mt in metric_types for f in EVALUATION_METRIC_FIELDS.get(mt, [])
    }

    for name in st.session_state.get("evaluation_forms", []):
        slug = name.replace(" ", "_")
        prefix = f"evaluation_{slug}_"
        approved_same = bool(
            st.session_state.get(f"{prefix}evaluated_same_as_approved", False),
        )

        for key, props in eval_section.items():
            if key in metric_keys or key in skip_fields:
                continue
            if approved_same and key in {
                "evaluated_by_name",
                "evaluated_by_institution",
                "evaluated_by_contact_email",
            }:
                continue
            if _field_required_for_task(props, current_task) and is_empty(
                st.session_state.get(f"{prefix}{key}"),
            ):
                missing.append(
                    (
                        "evaluation_data_methodology_results_commisioning",
                        f"{_label_for(props, key)} (Eval: {name})",
                    ),
                )

        for metric_type in metric_types:
            _validate_metric_group(
                prefix,
                slug,
                name,
                metric_type,
                eval_section,
                missing,
            )
    return missing


def validate_required_fields(
    schema: dict[str, dict[str, dict[str, Any]]],
    current_task: str | None = None,
) -> list[MissingItem]:
    """
    Run all validation passes and return missing fields.

    :param schema: The model card schema.
    :type schema: dict[str, dict[str, dict[str, Any]]]
    :param current_task: The current task identifier, defaults to None.
    :type current_task: str | None, optional
    :return: A list of missing items.
    :rtype: list[MissingItem]
    """
    return (
        validate_static_fields(schema, current_task)
        + validate_learning_architectures(schema)
        + validate_modalities_fields()
        + validate_evaluation_forms(schema, current_task)
    )
