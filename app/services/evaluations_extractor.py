
"""Module for handling evaluations extraction from Streamlit session state."""
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, cast

import streamlit as st

from app.core.collections import insert_after, insert_dict_after
from app.core.model_card.constants import (
    DATA_INPUT_OUTPUT_TS,
    EVALUATION_METRIC_FIELDS,
    SCHEMA,
    TASK_METRIC_MAP,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

_METRIC_SUFFIX_RE = re.compile(r"(?: \d+)$")


def _metric_base_name(name: str) -> str:
    """Remove trailing ' #n' suffix from a metric label."""
    return _METRIC_SUFFIX_RE.sub("", str(name or ""))

def extract_evaluations_from_state() -> list[dict[str, Any]]:  # noqa: C901, PLR0912, PLR0915
    """
    Extract evaluations from session state using the app schema.

    :return: A list of evaluation dicts ready to be serialized.
    :rtype: list[dict[str, Any]]
    """
    evaluations: list[dict[str, Any]] = []
    eval_forms = st.session_state.get("evaluation_forms", [])
    task = st.session_state.get("task", "Other")

    for name in eval_forms:
        slug = name.replace(" ", "_")
        prefix = f"evaluation_{slug}_"
        nested_prefix = f"evaluation_{slug}."
        evaluation: dict[str, Any] = {"name": name}

        eval_section = SCHEMA.get("evaluation_data", {})

        if isinstance(eval_section, dict):
            iter_fields: list[str] = []
            for field, props in eval_section.items():
                allowed = props.get("model_types")
                if allowed is None or task in allowed:
                    iter_fields.append(field)
        else:
            # evaluation_data in SCHEMA may be a sequence of field
            # names; cast for static type checkers
            iter_fields = list(cast("Iterable[str]", eval_section or []))

        for field in iter_fields:
            key = prefix + field
            if field.startswith("evaluated_by_") and field in evaluation:
                continue
            evaluation[field] = st.session_state.get(key, "")
            if evaluation.get("evaluated_same_as_approved", False):
                evaluation["evaluated_by_name"] = (
                    st.session_state.get(
                        "model_basic_information_clearance_approved_by_name",
                        "",
                    )
                )
                evaluation["evaluated_by_institution"] = (
                    st.session_state.get(
                        "model_basic_information_clearance_approved_by_institution",
                        "",
                    )
                )
                evaluation["evaluated_by_contact_email"] = (
                    st.session_state.get(
                        "model_basic_information_clearance_approved_by_contact_email",
                        "",
                    )
                )

        modality_entries: list[dict[str, str]] = []
        state = cast("Mapping[str, Any]", st.session_state)

        for key, value in state.items():
            if key.endswith("model_inputs") and isinstance(value, list):
                modality_entries.extend(
                    [
                        {"modality": item, "source": "model_inputs"}
                        for item in value
                    ],
                )
            elif key.endswith("model_outputs") and isinstance(value, list):
                modality_entries.extend(
                    [
                        {"modality": item, "source": "model_outputs"}
                        for item in value
                    ],
                )

        io_details: list[dict[str, Any]] = []
        counts: dict[tuple[str, str], int] = {}
        for entry in modality_entries:
            clean = entry["modality"].strip().replace(" ", "_").lower()
            source = entry["source"]
            pair = (clean, source)
            idx_for_pair = counts.get(pair, 0)
            counts[pair] = idx_for_pair + 1

            detail: dict[str, Any] = {
                "entry": entry["modality"],
                "source": source,
            }
            for field in DATA_INPUT_OUTPUT_TS:
                k = f"{prefix}{clean}_{source}_{idx_for_pair}_{field}"
                val = (
                    st.session_state.get(k)
                    or st.session_state.get(f"_{k}")
                    or st.session_state.get(f"__{k}")
                    or ""
                )
                detail[field] = val
            io_details.append(detail)


        evaluation = insert_after(
            evaluation,
            "inputs_outputs_technical_specifications",
            io_details,
            "url_info",
        )

        metric_dic: dict[str, list[dict[str, Any]]] = {}
        for metric_key in TASK_METRIC_MAP.get(task, []):
            type_list_key = f"{prefix}{metric_key}_list"
            metric_entries = st.session_state.get(type_list_key, [])
            metric_dic[metric_key] = []

            for metric_id in metric_entries:
                base_name = _metric_base_name(metric_id)
                entry2: dict[str, Any] = {"name": base_name}
                for field in EVALUATION_METRIC_FIELDS[metric_key]:
                    full_key = f"{nested_prefix}{metric_id}_{field}"
                    entry2[field] = st.session_state.get(full_key, "")
                metric_dic[metric_key].append(entry2)


        evaluation = insert_dict_after(
            evaluation,
            metric_dic,
            "additional_patient_info_ev",
        )

        evaluations.append(evaluation)

    return evaluations
