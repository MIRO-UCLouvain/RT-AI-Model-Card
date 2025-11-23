"""Training Data page for the Model Cards Writing Tool."""

from __future__ import annotations

from typing import Any, TypedDict, cast

import streamlit as st

from app.services import schema_loader
from app.ui.forms.render import (
    FieldProps,
    render_field,
    render_image_field,
    should_render,
)
from app.ui.utils.typography import (
    light_header_italics,
    section_divider,
    strip_brackets,
    subtitle,
    title,
    title_header,
)

TITLE = "Training data, methodology, and information"
SUBTITLE = (
    "containing all information about training and validation data "
    "(in case of a fine-tuned model, this section contains information "
    "about the tuning dataset)"
)
TITLE_FINE_TUNED = "Fine tuned from"
FINE_TUNED_INFO = (
    "These fields are only relevant for fine-tuned models. "
    "For tuned models, the training data will contain the tuning "
    "data information. Indicate N/A if not applicable."
)
TITLE_TRAINING_DATASET = "Training Dataset"
TRAINING_DATASET_INFO = (
    "Note that all fields refer to the raw training data used in "
    "'Model inputs' (i.e. before  pre-processing steps) and raw "
    "'Model outputs' for supervised models (i.e. after post-processing)"
)
TITLE_DATASET_GENERAL_INFO = "1. General information"
TITLE_DATASET_TECHNICAL_CHARACTERISTICS = "2. Technical characteristics"
TECHNICAL_CHARACTERISTICS_INFO = (
    "(i.e. image acquisition protocol, treatment details, …)"
)
MODEL_IO_WARNING = (
    "Start by adding model inputs and outputs "
    "in the previous section to enable technical details."
)
TITLE_PATIENT_INFO = "3. Patient demographics and clinical characteristics"
TITLE_TRAINING_METHODOLOGY = "Training Methodology"

SECTION_PREFIX = "training_data"


class TrainingData(TypedDict, total=False):
    """
    TypedDict for the 'Training Data' section.

    :param TypedDict: The base class for TypedDicts
    :type TypedDict: type
    :param total: If True, all fields are required, defaults to False
    :type total: bool, optional
    """

    model_name: FieldProps
    url_doi_to_model_card: FieldProps
    tuning_technique: FieldProps

    total_size: FieldProps
    number_of_patients: FieldProps
    source: FieldProps
    acquisition_period: FieldProps
    inclusion_exclusion_criteria: FieldProps
    type_of_data_augmentation: FieldProps
    strategy_for_data_augmentation: FieldProps
    url_info: FieldProps

    image_resolution: FieldProps
    patient_positioning: FieldProps
    scanner_model: FieldProps
    scan_acquisition_parameters: FieldProps
    scan_reconstruction_parameters: FieldProps
    fov: FieldProps

    treatment_modality_train: FieldProps
    beam_configuration_energy: FieldProps
    dose_engine: FieldProps
    target_volumes_and_prescription: FieldProps
    number_of_fractions: FieldProps

    reference_standard: FieldProps
    reference_standard_qa: FieldProps
    reference_standard_qa_additional_information: FieldProps

    icd10_11: FieldProps
    tnm_staging: FieldProps
    age: FieldProps
    sex: FieldProps
    target_volume_cm3: FieldProps
    bmi: FieldProps
    additional_patient_info: FieldProps

    validation_strategy: FieldProps
    validation_data_partition: FieldProps
    weights_initialization: FieldProps
    epochs: FieldProps
    optimiser: FieldProps
    learning_rate: FieldProps

    train_and_validation_loss_curves: FieldProps
    model_choice_criteria: FieldProps
    inference_method: FieldProps


def _render_fine_tuned_from(section: TrainingData) -> None:
    title_header(TITLE_FINE_TUNED)
    light_header_italics(FINE_TUNED_INFO)
    col1, col2, col3 = st.columns([1, 1.5, 1.5])
    with col1:
        render_field(
            "model_name",
            section["model_name"],
            SECTION_PREFIX,
        )
    with col2:
        render_field(
            "url_doi_to_model_card",
            section["url_doi_to_model_card"],
            SECTION_PREFIX,
        )
    with col3:
        render_field(
            "tuning_technique",
            section["tuning_technique"],
            SECTION_PREFIX,
        )


def _render_general_info(section: TrainingData) -> None:
    section_divider()
    title_header(TITLE_TRAINING_DATASET, size="1.2rem")
    light_header_italics(TRAINING_DATASET_INFO)
    title_header(TITLE_DATASET_GENERAL_INFO)

    col1, col2 = st.columns([1, 1])
    with col1:
        render_field(
            "total_size",
            section["total_size"],
            SECTION_PREFIX,
        )
    with col2:
        render_field(
            "number_of_patients",
            section["number_of_patients"],
            SECTION_PREFIX,
        )

    render_field(
        "source",
        section["source"],
        SECTION_PREFIX,
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        render_field(
            "acquisition_period",
            section["acquisition_period"],
            SECTION_PREFIX,
        )
    with col2:
        render_field(
            "inclusion_exclusion_criteria",
            section["inclusion_exclusion_criteria"],
            SECTION_PREFIX,
        )

    render_field(
        "type_of_data_augmentation",
        section["type_of_data_augmentation"],
        SECTION_PREFIX,
    )
    render_field(
        "strategy_for_data_augmentation",
        section["strategy_for_data_augmentation"],
        SECTION_PREFIX,
    )
    render_field(
        "url_info",
        section["url_info"],
        SECTION_PREFIX,
    )


def _render_technical_characteristics(section: TrainingData) -> None:
    section_divider()
    title_header("2. Technical characteristics")
    light_header_italics(TECHNICAL_CHARACTERISTICS_INFO)
    modality_entries: list[dict[str, str]] = []
    for key, value in st.session_state.items():
        if (
            isinstance(key, str)
            and key.endswith("model_inputs")
            and isinstance(value, list)
        ):
            modality_entries.extend(
                {"modality": item, "source": "model_inputs"} for item in value
            )
        elif (
            isinstance(key, str)
            and key.endswith("model_outputs")
            and isinstance(value, list)
        ):
            modality_entries.extend(
                {"modality": item, "source": "model_outputs"} for item in value
            )

    if not modality_entries:
        st.warning(MODEL_IO_WARNING)
        return
    counts: dict[tuple[str, str], int] = {}

    tabs = st.tabs(
        [strip_brackets(m["modality"]) for m in modality_entries],
    )
    for tab_idx, entry in enumerate(modality_entries):
        modality, source = entry["modality"], entry["source"]
        with tabs[tab_idx]:
            clean_modality = modality.strip().replace(" ", "_").lower()

            pair = (clean_modality, source)
            idx_for_pair = counts.get(pair, 0)
            counts[pair] = idx_for_pair + 1

            # sufijo único por modalidad + source + aparición
            suffix = f"{clean_modality}_{source}_{idx_for_pair}"

            title_header(
                f"{strip_brackets(modality)} — "
                f"{source.replace('_', ' ').capitalize()}",
                size="1rem",
            )

            field_keys = {
                "image_resolution": section["image_resolution"],
                "patient_positioning": section["patient_positioning"],
                "scanner_model": section["scanner_model"],
                "scan_acquisition_parameters": section[
                    "scan_acquisition_parameters"
                ],
                "scan_reconstruction_parameters": section[
                    "scan_reconstruction_parameters"
                ],
                "fov": section["fov"],
            }
            for f in field_keys.values():
                f["placeholder"] = f.get(
                    "placeholder",
                    "N/A or NA if Not Applicable",
                )

            col1, col2 = st.columns([1, 1])
            with col1:
                render_field(
                    f"{suffix}_image_resolution",
                    field_keys["image_resolution"],
                    SECTION_PREFIX,
                )
            with col2:
                render_field(
                    f"{suffix}_patient_positioning",
                    field_keys["patient_positioning"],
                    SECTION_PREFIX,
                )

            render_field(
                f"{suffix}_scanner_model",
                field_keys["scanner_model"],
                SECTION_PREFIX,
            )

            col1, col2 = st.columns([1, 1])
            with col1:
                render_field(
                    f"{suffix}_scan_acquisition_parameters",
                    field_keys["scan_acquisition_parameters"],
                    SECTION_PREFIX,
                )
            with col2:
                render_field(
                    f"{suffix}_scan_reconstruction_parameters",
                    field_keys["scan_reconstruction_parameters"],
                    SECTION_PREFIX,
                )

            render_field(
                f"{suffix}_fov",
                field_keys["fov"],
                SECTION_PREFIX,
            )


def _render_dose_prediction_fields(section: TrainingData) -> None:
    task = st.session_state.get("task", "").strip().lower()
    if should_render(section["treatment_modality_train"], task):
        render_field(
            "treatment_modality_train",
            section["treatment_modality_train"],
            SECTION_PREFIX,
        )

    col1, col2 = st.columns([1.4, 1.6])
    with col1:
        if should_render(section["beam_configuration_energy"], task):
            render_field(
                "beam_configuration_energy",
                section["beam_configuration_energy"],
                SECTION_PREFIX,
            )
    with col2:
        if should_render(section["dose_engine"], task):
            render_field(
                "dose_engine",
                section["dose_engine"],
                SECTION_PREFIX,
            )

    col1, col2 = st.columns([2, 1.1])
    with col1:
        if should_render(section["target_volumes_and_prescription"], task):
            render_field(
                "target_volumes_and_prescription",
                section["target_volumes_and_prescription"],
                SECTION_PREFIX,
            )
    with col2:
        if should_render(section["number_of_fractions"], task):
            render_field(
                "number_of_fractions",
                section["number_of_fractions"],
                SECTION_PREFIX,
            )


def _render_reference_and_validation(section: TrainingData) -> None:
    section_divider()
    render_field(
        "reference_standard",
        section["reference_standard"],
        SECTION_PREFIX,
    )
    render_field(
        "reference_standard_qa",
        section["reference_standard_qa"],
        SECTION_PREFIX,
    )
    render_field(
        "reference_standard_qa_additional_information",
        section["reference_standard_qa_additional_information"],
        SECTION_PREFIX,
    )

    section_divider()
    title_header(TITLE_PATIENT_INFO)

    col1, col2 = st.columns([1, 1])
    with col1:
        render_field(
            "icd10_11",
            section["icd10_11"],
            SECTION_PREFIX,
        )
    with col2:
        render_field(
            "tnm_staging",
            section["tnm_staging"],
            SECTION_PREFIX,
        )

    col1, col2 = st.columns([1, 1])
    with col1:
        render_field(
            "age",
            section["age"],
            SECTION_PREFIX,
        )
    with col2:
        render_field(
            "sex",
            section["sex"],
            SECTION_PREFIX,
        )

    col1, col2 = st.columns([2.5, 1])
    with col1:
        render_field(
            "target_volume_cm3",
            section["target_volume_cm3"],
            SECTION_PREFIX,
        )
    with col2:
        render_field(
            "bmi",
            section["bmi"],
            SECTION_PREFIX,
        )

    render_field(
        "additional_patient_info",
        section["additional_patient_info"],
        SECTION_PREFIX,
    )
    section_divider()
    title_header(TITLE_TRAINING_METHODOLOGY, size="1.2rem")
    col1, col2, col3 = st.columns([1.7, 1.2, 1])
    with col1:
        render_field(
            "validation_strategy",
            section["validation_strategy"],
            SECTION_PREFIX,
        )
    with col2:
        render_field(
            "validation_data_partition",
            section["validation_data_partition"],
            SECTION_PREFIX,
        )
    with col3:
        render_field(
            "weights_initialization",
            section["weights_initialization"],
            SECTION_PREFIX,
        )

    col1, col2, col3 = st.columns([2, 1.1, 1])
    with col1:
        render_field(
            "epochs",
            section["epochs"],
            SECTION_PREFIX,
        )
    with col2:
        render_field(
            "optimiser",
            section["optimiser"],
            SECTION_PREFIX,
        )
    with col3:
        render_field(
            "learning_rate",
            section["learning_rate"],
            SECTION_PREFIX,
        )

    render_image_field(
        "train_and_validation_loss_curves",
        section["train_and_validation_loss_curves"],
        SECTION_PREFIX,
    )

    render_field(
        "model_choice_criteria",
        section["model_choice_criteria"],
        SECTION_PREFIX,
    )
    render_field(
        "inference_method",
        section["inference_method"],
        SECTION_PREFIX,
    )


def _render_navigation() -> None:
    """Render the navigation buttons."""
    st.markdown("<br>", unsafe_allow_html=True)
    col1, _, _, _, col5 = st.columns([1.5, 2, 4.3, 2, 1.1])
    with col1:
        if st.button("Previous"):
            from app.ui.screens.sections.technical_specifications import (  # noqa: PLC0415
                technical_specifications_render,
            )

            st.session_state.runpage = technical_specifications_render
            st.rerun()
    with col5:
        if st.button("Next"):
            from app.ui.screens.sections.evaluation_data_mrc import (  # noqa: PLC0415
                evaluation_data_mrc_render,
            )

            st.session_state.runpage = evaluation_data_mrc_render
            st.rerun()


def training_data_render() -> None:
    """Render the Training Data page."""
    from app.ui.components.sidebar import sidebar_render  # noqa: PLC0415

    sidebar_render()

    schema_any: dict[str, Any] = schema_loader.get_model_card_schema()
    section = cast("TrainingData", schema_any[SECTION_PREFIX])

    title(TITLE)
    subtitle(SUBTITLE)

    _render_fine_tuned_from(section)
    _render_general_info(section)
    _render_technical_characteristics(section)
    _render_dose_prediction_fields(section)
    _render_reference_and_validation(section)
    _render_navigation()
