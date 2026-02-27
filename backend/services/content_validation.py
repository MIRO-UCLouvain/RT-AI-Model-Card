"""Server-side validation for model card content.

Two levels of validation:

1. **Structural** (``validate_content_structure``): enforced on every save.
   Checks that *content* is a non-empty dict whose top-level keys are
   recognised model card sections.  This catches clearly malformed payloads
   without rejecting incomplete drafts.

2. **Required-field** (``validate_content_for_publication``): enforced when
   a version is submitted for review.  Checks that the universally required
   fields (i.e. those not gated by a specific task type) are present and
   non-empty.  Task-specific required fields are validated when the parent
   card's *task_type* matches.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

# ── Expected top-level sections ──────────────────────────────────────────────

VALID_SECTIONS: frozenset[str] = frozenset(
    {
        "card_metadata",
        "model_basic_information",
        "technical_specifications",
        "learning_architecture",
        "learning_architectures",
        "hw_and_sw",
        "training_data",
        "evaluation_data_methodology_results_commisioning",
        "evaluations",
        "other_considerations",
        "appendix",
        # Frontend also stores these at the top level:
        "task",
        "_images",
        "_appendix_meta",
    }
)

# ── Required fields per section (universal — not task-gated) ─────────────────
# Derived from app/core/schemas/model_card_schema.json where required=true
# and no model_types filter is present.

REQUIRED_FIELDS: dict[str, list[str]] = {
    "card_metadata": [
        "card_creation_date",
        "version_number",
        "version_changes",
    ],
    "model_basic_information": [
        "name",
        "creation_date",
        "version_number",
        "version_changes",
        "model_scope_summary",
        "model_scope_anatomical_site",
        "clearance_type",
        "clearance_approved_by_institution",
        "observed_limitations",
        "type_of_learning_architecture",
        "developed_by_institution",
        "conflict_of_interest",
        "software_license",
    ],
    "technical_specifications": [
        "model_pipeline_summary",
        "model_inputs",
        "model_outputs",
        "pre_processing",
        "post_processing",
    ],
}

# ── Task-specific required fields ────────────────────────────────────────────
# These are only enforced when the card's task_type matches.

TASK_REQUIRED_FIELDS: dict[str, dict[str, list[str]]] = {
    "Dose prediction": {
        "training_data": [
            "treatment_modality_train",
            "beam_configuration_energy",
            "dose_engine",
            "target_volumes_and_prescription",
            "number_of_fractions",
        ],
    },
    "Image-to-Image translation": {
        "evaluation_data_methodology_results_commisioning": [
            "sanity_check",
        ],
    },
}

_EMPTY_SENTINELS: tuple[Any, ...] = ("", None, [], {})


def _is_empty(value: object) -> bool:
    """Return True if *value* is considered empty for validation."""
    return value in _EMPTY_SENTINELS


# ── Public API ───────────────────────────────────────────────────────────────


def validate_content_structure(content: dict[str, Any]) -> None:
    """Raise 422 if *content* is structurally invalid.

    Enforced on every save (create card / create version).
    Only checks shape, not individual field completeness.
    """
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Model card content cannot be empty.",
        )

    unknown = set(content.keys()) - VALID_SECTIONS
    if unknown and not any(k in VALID_SECTIONS for k in content):
        # Every key is unrecognised — likely a completely wrong payload.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Model card content does not contain any recognised "
                f"sections. Expected at least one of: "
                f"{', '.join(sorted(VALID_SECTIONS - {'task', '_images', '_appendix_meta'}))}."
            ),
        )


def validate_content_for_publication(
    content: dict[str, Any],
    task_type: str | None = None,
) -> None:
    """Raise 422 if *content* is missing required fields for publication.

    Enforced when a version is submitted for review.

    Parameters
    ----------
    content:
        The model card content dict stored in the version.
    task_type:
        The parent card's task type (e.g. "Dose prediction").
        When provided, task-specific required fields are also checked.
    """
    missing: list[str] = []

    # Universal required fields.
    for section, fields in REQUIRED_FIELDS.items():
        section_data = content.get(section)
        if not isinstance(section_data, dict):
            missing.extend(f"{section}.{f}" for f in fields)
            continue
        for field in fields:
            if _is_empty(section_data.get(field)):
                missing.append(f"{section}.{field}")

    # Task-specific required fields.
    if task_type and task_type in TASK_REQUIRED_FIELDS:
        for section, fields in TASK_REQUIRED_FIELDS[task_type].items():
            section_data = content.get(section)
            if not isinstance(section_data, dict):
                missing.extend(f"{section}.{f}" for f in fields)
                continue
            for field in fields:
                if _is_empty(section_data.get(field)):
                    missing.append(f"{section}.{field}")

    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": (
                    "Cannot submit for publication: the following required "
                    "fields are missing or empty."
                ),
                "missing_fields": missing,
            },
        )
