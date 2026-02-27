"""Unit tests for services/content_validation.py.

Pure logic tests — no database, no HTTP, no external services.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from services.content_validation import (
    REQUIRED_FIELDS,
    TASK_REQUIRED_FIELDS,
    VALID_SECTIONS,
    validate_content_for_publication,
    validate_content_structure,
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _minimal_valid_content() -> dict:
    """Content that passes both structural and publication validation."""
    return {
        "card_metadata": {
            "card_creation_date": "20260101",
            "version_number": "1.0",
            "version_changes": "Initial version",
        },
        "model_basic_information": {
            "name": "Test Model",
            "creation_date": "20260101",
            "version_number": "01.00.0000",
            "version_changes": "NA",
            "model_scope_summary": "Auto-segmentation model",
            "model_scope_anatomical_site": "HN",
            "clearance_type": "Not approved for medical use",
            "clearance_approved_by_institution": "Test Institution",
            "observed_limitations": "None observed",
            "type_of_learning_architecture": "U-Net",
            "developed_by_institution": "Test University",
            "conflict_of_interest": "None",
            "software_license": "MIT",
        },
        "technical_specifications": {
            "model_pipeline_summary": "End-to-end segmentation",
            "model_inputs": "CT images",
            "model_outputs": "Segmentation masks",
            "pre_processing": "Normalization",
            "post_processing": "Thresholding",
        },
    }


# ── validate_content_structure ───────────────────────────────────────────────


class TestStructuralValidation:
    """Tests for validate_content_structure (enforced on every save)."""

    def test_empty_content_raises_422(self) -> None:
        with pytest.raises(HTTPException) as exc:
            validate_content_structure({})
        assert exc.value.status_code == 422

    def test_no_recognised_sections_raises_422(self) -> None:
        with pytest.raises(HTTPException) as exc:
            validate_content_structure({"foo": "bar", "baz": 123})
        assert exc.value.status_code == 422

    def test_single_valid_section_passes(self) -> None:
        validate_content_structure({"card_metadata": {"version_number": "1.0"}})

    def test_full_valid_content_passes(self) -> None:
        validate_content_structure(_minimal_valid_content())

    def test_mix_of_known_and_unknown_keys_passes(self) -> None:
        """Unknown keys are tolerated when at least one valid section exists."""
        validate_content_structure({
            "card_metadata": {"version_number": "1.0"},
            "unknown_section": {"foo": "bar"},
        })

    def test_task_key_alone_passes(self) -> None:
        """The 'task' key is a valid top-level key from the frontend."""
        validate_content_structure({"task": "Segmentation"})

    def test_valid_sections_constant_is_frozen(self) -> None:
        assert isinstance(VALID_SECTIONS, frozenset)


# ── validate_content_for_publication ─────────────────────────────────────────


class TestPublicationValidation:
    """Tests for validate_content_for_publication (enforced at submit)."""

    def test_complete_content_passes(self) -> None:
        validate_content_for_publication(_minimal_valid_content())

    def test_missing_card_metadata_section_lists_fields(self) -> None:
        content = _minimal_valid_content()
        del content["card_metadata"]
        with pytest.raises(HTTPException) as exc:
            validate_content_for_publication(content)
        assert exc.value.status_code == 422
        detail = exc.value.detail
        assert "missing_fields" in detail
        for field in REQUIRED_FIELDS["card_metadata"]:
            assert f"card_metadata.{field}" in detail["missing_fields"]

    def test_empty_required_field_detected(self) -> None:
        content = _minimal_valid_content()
        content["model_basic_information"]["name"] = ""
        with pytest.raises(HTTPException) as exc:
            validate_content_for_publication(content)
        assert exc.value.status_code == 422
        assert "model_basic_information.name" in exc.value.detail["missing_fields"]

    def test_none_required_field_detected(self) -> None:
        content = _minimal_valid_content()
        content["card_metadata"]["version_number"] = None
        with pytest.raises(HTTPException) as exc:
            validate_content_for_publication(content)
        assert "card_metadata.version_number" in exc.value.detail["missing_fields"]

    def test_missing_technical_specifications_section(self) -> None:
        content = _minimal_valid_content()
        del content["technical_specifications"]
        with pytest.raises(HTTPException) as exc:
            validate_content_for_publication(content)
        for field in REQUIRED_FIELDS["technical_specifications"]:
            assert f"technical_specifications.{field}" in exc.value.detail["missing_fields"]

    def test_dose_prediction_task_requires_extra_fields(self) -> None:
        content = _minimal_valid_content()
        # Add an empty training_data section.
        content["training_data"] = {}
        with pytest.raises(HTTPException) as exc:
            validate_content_for_publication(content, task_type="Dose prediction")
        missing = exc.value.detail["missing_fields"]
        for field in TASK_REQUIRED_FIELDS["Dose prediction"]["training_data"]:
            assert f"training_data.{field}" in missing

    def test_non_dose_task_skips_dose_fields(self) -> None:
        """Segmentation task should NOT require dose-specific training fields."""
        content = _minimal_valid_content()
        # No training_data section — that's fine for non-dose tasks
        # (training_data fields are not in REQUIRED_FIELDS, only TASK_REQUIRED)
        validate_content_for_publication(content, task_type="Segmentation")

    def test_error_detail_has_message_key(self) -> None:
        with pytest.raises(HTTPException) as exc:
            validate_content_for_publication({})
        detail = exc.value.detail
        assert "message" in detail
        assert "missing_fields" in detail
        assert isinstance(detail["missing_fields"], list)
        assert len(detail["missing_fields"]) > 0
