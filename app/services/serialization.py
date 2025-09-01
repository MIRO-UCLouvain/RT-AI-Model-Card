"""Module for serializing Streamlit session_state into a model card JSON string."""  # noqa: E501

from __future__ import annotations

import json
from collections import OrderedDict
from copy import deepcopy
from typing import Any, cast

import streamlit as st

from app.core.collections import insert_after
from app.core.model_card.constants import (
    DATA_INPUT_OUTPUT_TS,
    EVALUATION_METRIC_FIELDS,
    LEARNING_ARCHITECTURE,
    TASK_METRIC_MAP,
)
from app.services.evaluations_extractor import (
    extract_evaluations_from_state,
)


def _get_with_fallback(key: str) -> str:
    """
    Retrieve a session_state value with underscore fallbacks.

    :param key: The key to retrieve from session_state.
    :type key: str
    :return: The value from session_state or an empty string.
    :rtype: str
    """
    return cast(
        "str",
        (
            st.session_state.get(key)
            or st.session_state.get(f"_{key}")
            or ""
        ),
    )


def _iter_modalities() -> list[dict[str, str]]:
    """
    Collect modality entries from model_inputs / model_outputs lists.

    :return: A list of dictionaries containing modality and source information.
    :rtype: list[dict[str, str]]
    """
    out: list[dict[str, str]] = []
    for k, v in st.session_state.items():
        if isinstance(k, str) and isinstance(v, list):
            if k.endswith("model_inputs"):
                out.extend(
                    {"modality": item, "source": "model_inputs"} for item in v
                )
            elif k.endswith("model_outputs"):
                out.extend(
                    {"modality": item, "source": "model_outputs"} for item in v
                )
    return out


def _collect_raw_sections(
    schema: dict[str, Any],
    current_task: str | None,
) -> dict[str, dict[str, Any]]:
    """
    Build raw section dict from session_state using the schema.

    :param schema: The schema to use for building the raw sections.
    :type schema: dict[str, Any]
    :param current_task: The current task being processed.
    :type current_task: str | None
    :return: A dictionary containing the raw section data.
    :rtype: dict[str, dict[str, Any]]
    """
    raw: dict[str, dict[str, Any]] = {}
    for section, fields in schema.items():
        sect: dict[str, Any] = {}
        if isinstance(fields, list):
            for full_key in fields:
                sub = full_key.removeprefix(section + "_")
                sect[sub] = st.session_state.get(full_key, "")
        elif isinstance(fields, dict):
            for key, props in fields.items():
                allowed = props.get("model_types")
                if allowed is None or current_task in allowed:
                    sect[key] = st.session_state.get(f"{section}_{key}", "")
        raw[section] = sect
    return raw


def _build_learning_architectures() -> list[dict[str, Any]]:
    """
    Collect learning architectures from session_state.

    :return: A list of learning architecture dictionaries.
    :rtype: list[dict[str, Any]]
    """
    la_forms = st.session_state.get("learning_architecture_forms", {})
    out: list[dict[str, Any]] = []
    for i in range(len(la_forms)):
        prefix = f"learning_architecture_{i}_"
        arch = deepcopy(LEARNING_ARCHITECTURE)
        for field in arch:
            arch[field] = st.session_state.get(f"{prefix}{field}", arch[field])
        arch["id"] = cast("Any", i)
        out.append(arch)
    return out


def _base_structured(
    raw: dict[str, dict[str, Any]],
    current_task: str | None,
    learning_architectures: list[dict[str, Any]],
) -> OrderedDict[str, Any]:
    """
    Create the base ordered output with top-level sections.

    :param raw: The raw section data.
    :type raw: dict[str, dict[str, Any]]
    :param current_task: The current task being processed.
    :type current_task: str | None
    :param learning_architectures: The list of learning architectures.
    :type learning_architectures: list[dict[str, Any]]
    :return: The base structured output.
    :rtype: OrderedDict[str, Any]
    """
    structured: OrderedDict[str, Any] = OrderedDict()
    if current_task:
        structured["task"] = current_task

    for section in [
        "card_metadata",
        "model_basic_information",
        "technical_specifications",
    ]:
        if section in raw:
            structured[section] = raw[section]

    structured["technical_specifications"]["learning_architectures"] = (
        learning_architectures
    )

    if "hw_and_sw" in raw:
        structured["technical_specifications"]["hw_and_sw"] = raw["hw_and_sw"]

    if "training_data" in raw:
        structured["training_data"] = raw["training_data"]

    return structured


def _inject_training_iots(
    raw: dict[str, dict[str, Any]],
    structured: OrderedDict[str, Any],
) -> None:
    """
    Inject training inputs/outputs technical specifications
    into the structured output.

    :param raw: The raw section data.
    :type raw: dict[str, dict[str, Any]]
    :param structured: The structured output.
    :type structured: OrderedDict[str, Any]
    """  # noqa: D205
    io_details: list[dict[str, Any]] = []
    for entry in _iter_modalities():
        clean = entry["modality"].strip().replace(" ", "_").lower()
        src = entry["source"]
        detail = {"entry": entry["modality"], "source": src}
        for field in DATA_INPUT_OUTPUT_TS:
            detail[field] = _get_with_fallback(
                f"training_data_{clean}_{src}_{field}",
            )
        io_details.append(detail)

    raw.setdefault("training_data", {})
    raw["training_data"]["inputs_outputs_technical_specifications"] = (
        io_details
    )

    structured.setdefault("training_data", {})
    structured["training_data"] = insert_after(
        structured["training_data"],
        "inputs_outputs_technical_specifications",
        io_details,
        "url_info",
    )


def _attach_metrics(
    structured: OrderedDict[str, Any],
    current_task: str | None,
) -> None:
    """
    Attach per-evaluation metrics from session_state.

    :param structured: The structured output.
    :type structured: OrderedDict[str, Any]
    :param current_task: The current task being processed.
    :type current_task: str | None
    """
    structured["evaluations"] = extract_evaluations_from_state()
    task_norm = (current_task or "").strip().lower()

    for eval_form in structured.get("evaluations", []):
        name = eval_form.get("name", "")
        for metric_type in TASK_METRIC_MAP.get(task_norm, []):
            metrics: list[dict[str, Any]] = []
            list_key = f"evaluation_{name}_{metric_type}_list"
            for metric_name in st.session_state.get(list_key, []):
                m = {"name": metric_name}
                for field in EVALUATION_METRIC_FIELDS[metric_type]:
                    m[field] = _get_with_fallback(
                        f"evaluation_{name}_{metric_name}_{field}",
                    )
                metrics.append(m)
            if metrics:
                eval_form[metric_type] = metrics


def parse_into_json(schema: dict[str, Any]) -> str:
    """
    Parse the schema into a JSON string.

    :param schema: The schema to parse.
    :type schema: dict[str, Any]
    :return: The JSON string representation of the schema.
    :rtype: str
    """
    current_task = st.session_state.get("task")

    raw = _collect_raw_sections(schema, current_task)
    learning_architectures = _build_learning_architectures()
    structured = _base_structured(raw, current_task, learning_architectures)

    _inject_training_iots(raw, structured)
    _attach_metrics(structured, current_task)

    if "other_considerations" in raw:
        structured["other_considerations"] = raw["other_considerations"]

    return json.dumps(structured, indent=2)
