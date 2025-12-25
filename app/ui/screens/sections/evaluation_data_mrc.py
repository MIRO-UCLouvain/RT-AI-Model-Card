"""Evaluation data, methodology, and results / commissioning page."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, TypedDict, cast

import streamlit as st

from app.services import schema_loader
from app.services.state_store import load_value, store_value
from app.ui.forms.render import (
    FieldProps,
    has_renderable_fields,
    render_field,
    render_fields,
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
    title_header_grey,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

TITLE = "Evaluation data, methodology, and results / commissioning"
SUBTITLE = (
    "containing all info about the evaluation data and procedure. "
    "Because it is common to evaluate your model on a different dataset, "
    "this section can be repeated as many times as needed. We refer to "
    "evaluation results for models that are evaluated but not necessarily "
    "with a clinical implementation in mind, and commissioning for models "
    "that are specifically evaluated within a clinical environment with "
    "clinic-specific data."
)
SAME_AS_APPROVED_BY_INFO = (
    "Evaluation team is the same as the approval team. Fields auto-filled."
)
EVALUATION_DATASET_INFO = (
    "Note that all fields refer to the raw evaluation data used in 'Model "
    "inputs' (i.e. before  pre-processing steps) and raw 'Model outputs' for "
    "supervised models (i.e. after post-processing)."
)
TITLE_EVALUATION_DATASET = "Evaluation Dataset"
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
WARNING_EVAL_EXISTS = "An evaluation form with this name already exists."
TITLE_QUANTITATIVE_EVALUATION = "Quantitative Evaluation"
TITLE_QUALITATIVE_EVALUATION = "Qualitative Evaluation"
NA_PLACEHOLDER = "N/A or NA if Not Applicable"
# This page renders dynamic forms with prefixes like "evaluation_<name>", so no
# single SECTION_PREFIX.

FieldName = Literal[
    "image_resolution",
    "patient_positioning",
    "scanner_model",
    "scan_acquisition_parameters",
    "scan_reconstruction_parameters",
    "fov",
]

class Evaluation(TypedDict, total=False):
    """
    TypedDict for each Evaluation form.

    :param TypedDict: The base class for TypedDicts
    :type TypedDict: _type_
    :param total: If True, all fields are required, defaults to False
    :type total: bool, optional
    """

    # Evaluation date
    evaluation_date: FieldProps

    # Evaluated by
    evaluated_by_name: FieldProps
    evaluated_by_institution: FieldProps
    evaluated_by_contact_email: FieldProps

    # Evaluation frame and sanity check
    evaluation_frame: FieldProps
    sanity_check: FieldProps

    # General information
    total_size: FieldProps
    number_of_patients: FieldProps
    source: FieldProps
    acquisition_period: FieldProps
    inclusion_exclusion_criteria: FieldProps
    url_info: FieldProps

    # Technical characteristics (per-modality rendering)
    image_resolution: FieldProps
    patient_positioning: FieldProps
    scanner_model: FieldProps
    scan_acquisition_parameters: FieldProps
    scan_reconstruction_parameters: FieldProps
    fov: FieldProps

    # Dose prediction task - specifics
    treatment_modality_eval: FieldProps
    beam_configuration_energy: FieldProps
    dose_engine: FieldProps
    target_volumes_and_prescription: FieldProps
    number_of_fractions: FieldProps

    # Reference standard
    reference_standard: FieldProps
    reference_standard_qa: FieldProps
    reference_standard_qa_additional_information: FieldProps

    # Patient demographics
    icd10_11_ev: FieldProps
    tnm_staging_ev: FieldProps
    age_ev: FieldProps
    sex_ev: FieldProps
    target_volume_cm3_ev: FieldProps
    bmi_ev: FieldProps
    additional_patient_info_ev: FieldProps

    # Image-to-image translation metrics - Image Similarity Metrics
    type_ism: FieldProps
    on_volume_ism: FieldProps
    registration_ism: FieldProps
    sample_data_ism: FieldProps
    mean_data_ism: FieldProps
    figure_ism: FieldProps

    # Image-to-image translation metrics - Dose Metrics
    type_dose_dm: FieldProps
    metric_specifications_dm: FieldProps
    on_volume_dm: FieldProps
    registration_dm: FieldProps
    treatment_modality_dm: FieldProps
    dose_engine_dm: FieldProps
    dose_grid_resolution_dm: FieldProps
    tps_vendor_dm: FieldProps
    sample_data_dm: FieldProps
    mean_data_dm: FieldProps
    figure_dm: FieldProps

    # Segmentation - Geometric Metrics
    type_gm_seg: FieldProps
    metric_specifications_gm_seg: FieldProps
    on_volume_gm_seg: FieldProps
    sample_data_gm_seg: FieldProps
    mean_data_gm_seg: FieldProps
    figure_gm_seg: FieldProps

    # Segmentation - Dose Metrics
    type_dose_dm_seg: FieldProps
    metric_specifications_dm_seg: FieldProps
    on_volume_dm_seg: FieldProps
    treatment_modality_dm_seg: FieldProps
    dose_engine_dm_seg: FieldProps
    dose_grid_resolution_dm_seg: FieldProps
    tps_vendor_dm_seg: FieldProps
    sample_data_dm_seg: FieldProps
    mean_data_dm_seg: FieldProps
    figure_dm_seg: FieldProps

    iov_method_seg: FieldProps
    iov_results_seg: FieldProps

    # Dose prediction - Dose Metrics
    type_dose_dm_dp: FieldProps
    metric_specifications_dm_dp: FieldProps
    on_volume_dm_dp: FieldProps
    dose_grid_resolution_dm_dp: FieldProps
    sample_data_dm_dp: FieldProps
    mean_data_dm_dp: FieldProps
    figure_dm_dp: FieldProps

    # Other - Metrics
    type_metrics_other: FieldProps
    additional_info_other: FieldProps
    sample_data_other: FieldProps
    mean_data_other: FieldProps
    figure_other: FieldProps

    # Uncertainty & other
    uncertainty_metrics_method: FieldProps
    uncertainty_metrics_results: FieldProps
    other_method: FieldProps
    other_results: FieldProps

    # Qualitative evaluation
    evaluators_information: FieldProps
    likert_scoring_method: FieldProps
    likert_scoring_results: FieldProps
    turing_test_method: FieldProps
    turing_test_results: FieldProps
    time_saving_method: FieldProps
    time_saving_results: FieldProps
    qualitative_other_method: FieldProps
    qualitative_other_results: FieldProps
    explainability: FieldProps
    citation_details: FieldProps


def _render_header_and_evaluated_by(
    section: Evaluation,
    section_prefix: str,
) -> None:
    """
    Render the header and evaluated by fields for the evaluation section.

    :param section: The evaluation section data.
    :type section: Evaluation
    :param section_prefix: The prefix for the section fields.
    :type section_prefix: str
    """
    if "evaluation_date" in section:
        render_field(
            "evaluation_date",
            section["evaluation_date"],
            section_prefix,
        )

    section_divider()
    title_header("Evaluated by")

    same_key = f"{section_prefix}_evaluated_same_as_approved"
    load_value(same_key, 0)
    same = st.checkbox(
        "Same as 'Approved by'",
        key="_" + same_key,
        on_change=store_value,
        args=(same_key,),
    )

    if not same:
        if all(
            k in section
            for k in (
                "evaluated_by_name",
                "evaluated_by_institution",
                "evaluated_by_contact_email",
            )
        ):
            col1, col2, col3 = st.columns([1, 1.5, 1.5])
            with col1:
                render_field(
                    "evaluated_by_name",
                    section["evaluated_by_name"],
                    section_prefix,
                )
            with col2:
                render_field(
                    "evaluated_by_institution",
                    section["evaluated_by_institution"],
                    section_prefix,
                )
            with col3:
                render_field(
                    "evaluated_by_contact_email",
                    section["evaluated_by_contact_email"],
                    section_prefix,
                )
    else:
        st.info(SAME_AS_APPROVED_BY_INFO)

    section_divider()
    render_fields(
        ["evaluation_frame", "sanity_check"],
        cast("dict[str, FieldProps]", section),
        section_prefix,
        st.session_state.get("task", ""),
    )


def _render_general_info(section: Evaluation, section_prefix: str) -> None:
    """
    Render general information fields for the evaluation section.

    :param section: The evaluation section data.
    :type section: Evaluation
    :param section_prefix: The prefix for the section fields.
    :type section_prefix: str
    """
    section_divider()
    title_header(TITLE_EVALUATION_DATASET, size="1.2rem")
    light_header_italics(EVALUATION_DATASET_INFO)
    title_header(TITLE_DATASET_GENERAL_INFO)

    col1, col2 = st.columns([1, 1])
    with col1:
        render_field(
            "total_size",
            section["total_size"],
            section_prefix,
        )
    with col2:
        render_field(
            "number_of_patients",
            section["number_of_patients"],
            section_prefix,
        )
    render_field(
        "source",
        section["source"],
        section_prefix,
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        render_field(
            "acquisition_period",
            section["acquisition_period"],
            section_prefix,
        )
    with col2:
        render_field(
            "inclusion_exclusion_criteria",
            section["inclusion_exclusion_criteria"],
            section_prefix,
        )
    render_field(
        "url_info",
        section["url_info"],
        section_prefix,
    )


def _render_technical_characteristics(  # noqa: C901, PLR0915
    section: Evaluation,
    section_prefix: str,
) -> None:
    """
    Render the technical characteristics fields for the evaluation section.
    Adds a toggle to reuse Training Dataset technical specs. When turned ON,
    values are copied into the evaluation keys and fields are shown disabled.
    When turned OFF after having autofilled, the evaluation keys are cleared.
    """  # noqa: D205
    section_divider()
    title_header(TITLE_DATASET_TECHNICAL_CHARACTERISTICS)
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

    # Evaluation-level checkbox
    same_ts_key = f"{section_prefix}_ts_same_as_training"
    autofilled_key = f"{section_prefix}_ts_autofilled"
    load_value(same_ts_key, 0)
    same_ts = st.checkbox(
        "Use Training Dataset technical characteristics for this "
        "*Evaluation Dataset*",
        key="_" + same_ts_key,
        on_change=store_value,
        args=(same_ts_key,),
    )

    def _iter_eval_field_keys() -> Iterator[tuple[int, str, str, FieldName]]:
        """Yield (idx, clean_modality, source, field_name) for all eval.

        Technical Specifications fields.
        """
        fields: tuple[FieldName, ...] = (
            "image_resolution",
            "patient_positioning",
            "scanner_model",
            "scan_acquisition_parameters",
            "scan_reconstruction_parameters",
            "fov",
        )

        counts: dict[tuple[str, str], int] = {}

        for entry in modality_entries:
            clean: str = entry["modality"].strip().replace(" ", "_").lower()
            source: str = entry["source"]
            pair = (clean, source)
            idx_for_pair = counts.get(pair, 0)
            counts[pair] = idx_for_pair + 1
            for field in fields:
                yield idx_for_pair, clean, source, field



    # Turned ON → copy training → eval and mark autofilled
    if same_ts:
        for idx_for_pair, clean, source, field in _iter_eval_field_keys():
            train_key = f"training_data_{clean}_{source}_{idx_for_pair}_{field}"  # noqa: E501
            eval_key = (
                f"{section_prefix}_{clean}_{source}_{idx_for_pair}_{field}"
            )
            st.session_state[eval_key] = st.session_state.get(train_key, "")
        st.session_state[autofilled_key] = True
        st.info(
            "Filled from Training Dataset (read-only). Uncheck to"
            " provide custom values.",
        )
    elif st.session_state.get(autofilled_key):
        for idx_for_pair, clean, source, field in _iter_eval_field_keys():
            eval_key = (
                f"{section_prefix}_{clean}_{source}_{idx_for_pair}_{field}"
            )
            st.session_state[eval_key] = ""
        st.session_state[autofilled_key] = False


    tabs = st.tabs([strip_brackets(m["modality"]) for m in modality_entries])
    counts: dict[tuple[str, str], int] = {}

    for tab_idx, entry in enumerate(modality_entries):
        modality, source = entry["modality"], entry["source"]
        with tabs[tab_idx]:
            clean_modality = modality.strip().replace(" ", "_").lower()
            heading = (
                f"{strip_brackets(modality)} — "
                f"{source.replace('_', ' ').capitalize()}"
            )
            title_header(heading, size="1rem")

            pair = (clean_modality, source)
            idx_for_pair = counts.get(pair, 0)
            counts[pair] = idx_for_pair + 1
            suffix = f"{clean_modality}_{source}_{idx_for_pair}"

            disabled_flag = {"disabled": True} if same_ts else {}

            field_keys = {
                "image_resolution": {
                    **section["image_resolution"],
                    **disabled_flag,
                },
                "patient_positioning": {
                    **section["patient_positioning"],
                    **disabled_flag,
                },
                "scanner_model": {
                    **section["scanner_model"],
                    **disabled_flag,
                },
                "scan_acquisition_parameters": {
                    **section["scan_acquisition_parameters"],
                    **disabled_flag,
                },
                "scan_reconstruction_parameters": {
                    **section["scan_reconstruction_parameters"],
                    **disabled_flag,
                },
                "fov": {
                    **section["fov"],
                    **disabled_flag,
                },
            }
            for f in field_keys.values():
                f["placeholder"] = f.get("placeholder", NA_PLACEHOLDER)

            col1, col2 = st.columns([1, 1])
            with col1:
                render_field(
                    f"{suffix}_image_resolution",
                    cast("FieldProps", field_keys["image_resolution"]),
                    section_prefix,
                )
            with col2:
                render_field(
                    f"{suffix}_patient_positioning",
                    cast("FieldProps", field_keys["patient_positioning"]),
                    section_prefix,
                )

            render_field(
                f"{suffix}_scanner_model",
                cast("FieldProps", field_keys["scanner_model"]),
                section_prefix,
            )

            col1, col2 = st.columns([1, 1])
            with col1:
                scan_acq_props = cast(
                    "FieldProps",
                    field_keys["scan_acquisition_parameters"],
                )
                render_field(
                    f"{suffix}_scan_acquisition_parameters",
                    scan_acq_props,
                    section_prefix,
                )
            with col2:
                scan_recon_props = cast(
                    "FieldProps",
                    field_keys["scan_reconstruction_parameters"],
                )
                render_field(
                    f"{suffix}_scan_reconstruction_parameters",
                    scan_recon_props,
                    section_prefix,
                )

            render_field(
                f"{suffix}_fov",
                cast("FieldProps", field_keys["fov"]),
                section_prefix,
            )

            for f in field_keys.values():
                f["placeholder"] = f.get("placeholder", NA_PLACEHOLDER)

def _render_dose_prediction_eval(
    section: Evaluation,
    section_prefix: str,
    current_task: str,
) -> None:
    """
    Render the dose prediction evaluation fields.

    :param section: The evaluation section data.
    :type section: Evaluation
    :param section_prefix: The prefix for the section fields.
    :type section_prefix: str
    :param current_task: The current task being evaluated (Dose prediction).
    :type current_task: str
    """
    # Exclusive to Dose prediction task
    if should_render(section["treatment_modality_eval"], current_task):
        render_field(
            "treatment_modality_eval",
            section["treatment_modality_eval"],
            section_prefix,
        )

    col1, col2 = st.columns([1.4, 1.6])
    with col1:
        if should_render(section["beam_configuration_energy"], current_task):
            render_field(
                "beam_configuration_energy",
                section["beam_configuration_energy"],
                section_prefix,
            )
    with col2:
        if should_render(section["dose_engine"], current_task):
            render_field(
                "dose_engine",
                section["dose_engine"],
                section_prefix,
            )

    col1, col2 = st.columns([1, 1])
    with col1:
        if should_render(
            section["target_volumes_and_prescription"],
            current_task,
        ):
            render_field(
                "target_volumes_and_prescription",
                section["target_volumes_and_prescription"],
                section_prefix,
            )
    with col2:
        if should_render(section["number_of_fractions"], current_task):
            render_field(
                "number_of_fractions",
                section["number_of_fractions"],
                section_prefix,
            )


def _render_reference_and_demographics(
    section: Evaluation,
    section_prefix: str,
    current_task: str,
) -> None:
    """
    Render the reference and demographics information.

    :param section: The evaluation section containing the data.
    :type section: Evaluation
    :param section_prefix: The prefix for the section fields.
    :type section_prefix: str
    :param current_task: The current task being evaluated.
    :type current_task: str
    """
    section_divider()
    render_fields(
        [
            "reference_standard",
            "reference_standard_qa",
            "reference_standard_qa_additional_information",
        ],
        cast("dict[str, FieldProps]", section),
        section_prefix,
        current_task,
    )

    title_header(TITLE_PATIENT_INFO)
    col1, col2 = st.columns([1, 1])
    with col1:
        render_field(
            "icd10_11_ev",
            section["icd10_11_ev"],
            section_prefix,
        )
    with col2:
        render_field(
            "tnm_staging_ev",
            section["tnm_staging_ev"],
            section_prefix,
        )

    col1, col2 = st.columns([1, 1])
    with col1:
        render_field(
            "age_ev",
            section["age_ev"],
            section_prefix,
        )
    with col2:
        render_field(
            "sex_ev",
            section["sex_ev"],
            section_prefix,
        )

    col1, col2 = st.columns([1, 1])
    with col1:
        render_field(
            "target_volume_cm3_ev",
            section["target_volume_cm3_ev"],
            section_prefix,
        )
    with col2:
        render_field(
            "bmi_ev",
            section["bmi_ev"],
            section_prefix,
        )

    render_field(
        "additional_patient_info_ev",
        section["additional_patient_info_ev"],
        section_prefix,
    )


def _render_image_similarity_metrics_block(
    section: Evaluation,
    section_prefix: str,
    current_task: str,
) -> None:
    """
    Render the Image Similarity Metrics block for Image-to-image translation
    task.

    :param section: The evaluation section containing the metrics.
    :type section: Evaluation
    :param section_prefix: The prefix for the section fields.
    :type section_prefix: str
    :param current_task: The current task being evaluated (Image-to-image translation).
    :type current_task: str
    """  # noqa: D205, E501
    image_similarity_metrics_fields = [
        "on_volume_ism",
        "registration_ism",
        "sample_data_ism",
        "mean_data_ism",
        "figure_ism",
    ]
    task = st.session_state.get("task", "").strip().lower()
    if should_render(section["type_ism"], task):
        title_header("Image Similarity Metrics")
        render_field("type_ism", section["type_ism"], section_prefix)

    ism_entries = st.session_state.get(f"{section_prefix}_type_ism_list", [])
    if not ism_entries or not has_renderable_fields(
        image_similarity_metrics_fields,
        cast("dict[str, FieldProps]", section),
        current_task,
    ):
        return

    tabs = st.tabs(ism_entries)
    for tab, type_name in zip(tabs, ism_entries, strict=False):
        with tab:
            sub_prefix = f"{section_prefix}.{type_name}"
            task = st.session_state.get("task", "").strip().lower()
            col1, col2 = st.columns([1, 1])
            with col1:
                if should_render(section["on_volume_ism"], task):
                    render_field(
                        "on_volume_ism",
                        section["on_volume_ism"],
                        sub_prefix,
                    )
            with col2:
                if should_render(section["registration_ism"], task):
                    render_field(
                        "registration_ism",
                        section["registration_ism"],
                        sub_prefix,
                    )
            if should_render(section["sample_data_ism"], task):
                render_field(
                    "sample_data_ism",
                    section["sample_data_ism"],
                    sub_prefix,
                )
            if should_render(section["mean_data_ism"], task):
                render_field(
                    "mean_data_ism",
                    section["mean_data_ism"],
                    sub_prefix,
                )
            if should_render(section["figure_ism"], task):
                render_image_field(
                    "figure_ism",
                    section["figure_ism"],
                    sub_prefix,
                )


def _render_image_dose_metrics_block(  # noqa: C901, PLR0912
    section: Evaluation,
    section_prefix: str,
    current_task: str,
) -> None:
    """
    Render the Dose Metrics block for Image-to-image translation task.

    :param section: The evaluation section containing the metrics.
    :type section: Evaluation
    :param section_prefix: The prefix for the section fields.
    :type section_prefix: str
    :param current_task: The current task being evaluated (Image-to-image translation).
    :type current_task: str
    """  # noqa: E501
    image_dose_metrics_fields = [
        "metric_specifications_dm",
        "on_volume_dm",
        "registration_dm",
        "treatment_modality_dm",
        "dose_engine_dm",
        "dose_grid_resolution_dm",
        "tps_vendor_dm",
        "sample_data_dm",
        "mean_data_dm",
        "figure_dm",
    ]
    if should_render(section["type_dose_dm"], current_task):
        section_divider()
        title_header("Dose Metrics")
        render_field("type_dose_dm", section["type_dose_dm"], section_prefix)

    dm_entries = st.session_state.get(
        f"{section_prefix}_type_dose_dm_list",
        [],
    )
    if not dm_entries or not has_renderable_fields(
        image_dose_metrics_fields,
        cast("dict[str, FieldProps]", section),
        current_task,
    ):
        return

    tabs = st.tabs([str(entry) for entry in dm_entries if entry])
    for tab, dm_name in zip(tabs, dm_entries, strict=False):
        with tab:
            sub_prefix = f"{section_prefix}.{dm_name}"
            if should_render(
                section["metric_specifications_dm"], current_task,
            ):
                render_field(
                    "metric_specifications_dm",
                    section["metric_specifications_dm"],
                    sub_prefix,
                )
            col1, col2 = st.columns([1, 1])
            with col1:
                if should_render(section["on_volume_dm"], current_task):
                    render_field(
                        "on_volume_dm",
                        section["on_volume_dm"],
                        sub_prefix,
                    )
            with col2:
                if should_render(section["registration_dm"], current_task):
                    render_field(
                        "registration_dm",
                        section["registration_dm"],
                        sub_prefix,
                    )
            if should_render(section["treatment_modality_dm"], current_task):
                render_field(
                    "treatment_modality_dm",
                    section["treatment_modality_dm"],
                    sub_prefix,
                )
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if should_render(section["dose_engine_dm"], current_task):
                    render_field(
                        "dose_engine_dm",
                        section["dose_engine_dm"],
                        sub_prefix,
                    )
            with col2:
                if should_render(
                    section["dose_grid_resolution_dm"],
                    current_task,
                ):
                    render_field(
                        "dose_grid_resolution_dm",
                        section["dose_grid_resolution_dm"],
                        sub_prefix,
                    )
            with col3:
                if should_render(section["tps_vendor_dm"], current_task):
                    render_field(
                        "tps_vendor_dm",
                        section["tps_vendor_dm"],
                        sub_prefix,
                    )
            if should_render(section["sample_data_dm"], current_task):
                render_field(
                    "sample_data_dm",
                    section["sample_data_dm"],
                    sub_prefix,
                )
            if should_render(section["mean_data_dm"], current_task):
                render_field(
                    "mean_data_dm",
                    section["mean_data_dm"],
                    sub_prefix,
                )
            if should_render(section["figure_dm"], current_task):
                render_image_field(
                    "figure_dm",
                    section["figure_dm"],
                    sub_prefix,
                )


def _render_segmentation_geometric_block(
    section: Evaluation,
    section_prefix: str,
    current_task: str,
) -> None:
    """
    Render the Geometric metrics block for segmentation task.

    :param section: The evaluation section data.
    :type section: Evaluation
    :param section_prefix: The prefix for the section.
    :type section_prefix: str
    :param current_task: The current task being evaluated (Segmentation).
    :type current_task: str
    """
    if should_render(section["type_gm_seg"], current_task):
        title_header("Geometric Metrics")
        render_field("type_gm_seg", section["type_gm_seg"], section_prefix)

    geometric_metrics_segmentation_fields = [
        "metric_specifications_gm_seg",
        "on_volume_gm_seg",
        "sample_data_gm_seg",
        "mean_data_gm_seg",
        "figure_gm_seg",
    ]
    seg_entries = st.session_state.get(
        f"{section_prefix}_type_gm_seg_list",
        [],
    )
    if not seg_entries or not has_renderable_fields(
        geometric_metrics_segmentation_fields,
        cast("dict[str, FieldProps]", section),
        current_task,
    ):
        return

    tabs = st.tabs([str(entry) for entry in seg_entries if entry])
    for tab, seg_name in zip(tabs, seg_entries, strict=False):
        with tab:
            sub_prefix = f"{section_prefix}.{seg_name}"
            col1, col2 = st.columns([1, 1])
            with col1:
                render_field(
                    "metric_specifications_gm_seg",
                    section["metric_specifications_gm_seg"],
                    sub_prefix,
                )
            with col2:
                render_field(
                    "on_volume_gm_seg",
                    section["on_volume_gm_seg"],
                    sub_prefix,
                )
            render_field(
                "sample_data_gm_seg",
                section["sample_data_gm_seg"],
                sub_prefix,
            )
            render_field(
                "mean_data_gm_seg",
                section["mean_data_gm_seg"],
                sub_prefix,
            )
            render_image_field(
                "figure_gm_seg",
                section["figure_gm_seg"],
                sub_prefix,
            )


def _render_segmentation_dose_block(  # noqa: C901
    section: Evaluation,
    section_prefix: str,
    current_task: str,
) -> None:
    """
    Render the Dose metrics block for segmentation task.

    :param section: The evaluation section data.
    :type section: Evaluation
    :param section_prefix: The prefix for the section.
    :type section_prefix: str
    :param current_task: The current task being evaluated (Segmentation).
    :type current_task: str
    """
    if should_render(section["type_dose_dm_seg"], current_task):
        section_divider()
        title_header("Dose Metrics")
        render_field(
            "type_dose_dm_seg",
            section["type_dose_dm_seg"],
            section_prefix,
        )

    dose_metrics_segmentation_fields = [
        "metric_specifications_dm_seg",
        "on_volume_dm_seg",
        "treatment_modality_dm_seg",
        "dose_engine_dm_seg",
        "dose_grid_resolution_dm_seg",
        "tps_vendor_dm_seg",
        "sample_data_dm_seg",
        "mean_data_dm_seg",
        "figure_dm_seg",
    ]
    dm_seg_entries = st.session_state.get(
        f"{section_prefix}_type_dose_dm_seg_list",
        [],
    )
    if not dm_seg_entries or not has_renderable_fields(
        dose_metrics_segmentation_fields,
        cast("dict[str, FieldProps]", section),
        current_task,
    ):
        return

    tabs = st.tabs([str(entry) for entry in dm_seg_entries if entry])
    for tab, seg_name in zip(tabs, dm_seg_entries, strict=False):
        with tab:
            sub_prefix = f"{section_prefix}.{seg_name}"
            if should_render(
                section["metric_specifications_dm_seg"],
                current_task,
            ):
                render_field(
                    "metric_specifications_dm_seg",
                    section["metric_specifications_dm_seg"],
                    sub_prefix,
                )
            if should_render(section["on_volume_dm_seg"], current_task):
                render_field(
                    "on_volume_dm_seg",
                    section["on_volume_dm_seg"],
                    sub_prefix,
                )
            if should_render(
                section["treatment_modality_dm_seg"],
                current_task,
            ):
                render_field(
                    "treatment_modality_dm_seg",
                    section["treatment_modality_dm_seg"],
                    sub_prefix,
                )
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if should_render(section["dose_engine_dm_seg"], current_task):
                    render_field(
                        "dose_engine_dm_seg",
                        section["dose_engine_dm_seg"],
                        sub_prefix,
                    )
            with col2:
                if should_render(
                    section["dose_grid_resolution_dm_seg"],
                    current_task,
                ):
                    render_field(
                        "dose_grid_resolution_dm_seg",
                        section["dose_grid_resolution_dm_seg"],
                        sub_prefix,
                    )
            with col3:
                if should_render(section["tps_vendor_dm_seg"], current_task):
                    render_field(
                        "tps_vendor_dm_seg",
                        section["tps_vendor_dm_seg"],
                        sub_prefix,
                    )
            if should_render(section["sample_data_dm_seg"], current_task):
                render_field(
                    "sample_data_dm_seg",
                    section["sample_data_dm_seg"],
                    sub_prefix,
                )
            if should_render(section["mean_data_dm_seg"], current_task):
                render_field(
                    "mean_data_dm_seg",
                    section["mean_data_dm_seg"],
                    sub_prefix,
                )
            if should_render(section["figure_dm_seg"], current_task):
                render_image_field(
                    "figure_dm_seg",
                    section["figure_dm_seg"],
                    sub_prefix,
                )


def _render_iov_block(
    section: Evaluation,
    section_prefix: str,
    current_task: str,
) -> None:
    """
    Render the IOV (Inter-Observer Variability) block.

    :param section: The evaluation section containing the IOV metrics.
    :type section: Evaluation
    :param section_prefix: The prefix for the section.
    :type section_prefix: str
    :param current_task: The current task being evaluated (Segmentation).
    :type current_task: str
    """
    if not (
        should_render(section["iov_method_seg"], current_task)
        or should_render(section["iov_results_seg"], current_task)
    ):
        return

    section_divider()
    title_header("IOV (Inter-Observer Variability)")

    col1, col2 = st.columns([1, 1])
    with col1:
        if should_render(section["iov_method_seg"], current_task):
            render_field(
                "iov_method_seg",
                section["iov_method_seg"],
                section_prefix,
            )
    with col2:
        if should_render(section["iov_results_seg"], current_task):
            render_field(
                "iov_results_seg",
                section["iov_results_seg"],
                section_prefix,
            )


def _render_dose_prediction_dose_block(
    section: Evaluation,
    section_prefix: str,
    current_task: str,
) -> None:
    """
    Render the Dose Metrics block for Dose prediction task.

    :param section: The evaluation section containing the metrics.
    :type section: Evaluation
    :param section_prefix: The prefix for the section.
    :type section_prefix: str
    :param current_task: The current task being evaluated (Dose Prediction).
    :type current_task: str
    """
    dose_prediction_dose_metrics_fields = [
        "metric_specifications_dm_dp",
        "on_volume_dm_dp",
        "dose_grid_resolution_dm_dp",
        "sample_data_dm_dp",
        "mean_data_dm_dp",
        "figure_dm_dp",
    ]
    if should_render(section["type_dose_dm_dp"], current_task):
        title_header("Dose Metrics")
        render_field(
            "type_dose_dm_dp",
            section["type_dose_dm_dp"],
            section_prefix,
        )

    dm_dp_entries = st.session_state.get(
        f"{section_prefix}_type_dose_dm_dp_list",
        [],
    )
    if not dm_dp_entries or not has_renderable_fields(
        dose_prediction_dose_metrics_fields,
        cast("dict[str, FieldProps]", section),
        current_task,
    ):
        return

    tabs = st.tabs([str(entry) for entry in dm_dp_entries if entry])
    for tab, dp_name in zip(tabs, dm_dp_entries, strict=False):
        with tab:
            sub_prefix = f"{section_prefix}.{dp_name}"
            if should_render(
                section["metric_specifications_dm_dp"],
                current_task,
            ):
                render_field(
                    "metric_specifications_dm_dp",
                    section["metric_specifications_dm_dp"],
                    sub_prefix,
                )
            if should_render(section["on_volume_dm_dp"], current_task):
                render_field(
                    "on_volume_dm_dp",
                    section["on_volume_dm_dp"],
                    sub_prefix,
                )
            if should_render(
                section["dose_grid_resolution_dm_dp"],
                current_task,
            ):
                render_field(
                    "dose_grid_resolution_dm_dp",
                    section["dose_grid_resolution_dm_dp"],
                    sub_prefix,
                )
            if should_render(section["sample_data_dm_dp"], current_task):
                render_field(
                    "sample_data_dm_dp",
                    section["sample_data_dm_dp"],
                    sub_prefix,
                )
            if should_render(section["mean_data_dm_dp"], current_task):
                render_field(
                    "mean_data_dm_dp",
                    section["mean_data_dm_dp"],
                    sub_prefix,
                )
            if should_render(section["figure_dm_dp"], current_task):
                render_image_field(
                    "figure_dm_dp",
                    section["figure_dm_dp"],
                    sub_prefix,
                )


def _render_other_metrics(
    section: Evaluation,
    section_prefix: str,
    current_task: str,
) -> None:
    """
    Render the Other Metrics and Uncertainty block for the evaluation.

    :param section: The evaluation section containing the metrics.
    :type section: Evaluation
    :param section_prefix: The prefix for the section.
    :type section_prefix: str
    :param current_task: The current task being evaluated (Other).
    :type current_task: str
    """
    if should_render(section["type_metrics_other"], current_task):
        title_header("Other Metrics")
        render_field(
            "type_metrics_other",
            section["type_metrics_other"],
            section_prefix,
        )

    other_keys = st.session_state.get(
        f"{section_prefix}_type_metrics_other_list",
        [],
    )
    if other_keys:
        tabs = st.tabs(other_keys)
        for tab, name in zip(tabs, other_keys, strict=False):
            with tab:
                sub_prefix = f"{section_prefix}.{name}"
                render_field(
                    "additional_info_other",
                    section["additional_info_other"],
                    sub_prefix,
                )
                render_field(
                    "sample_data_other",
                    section["sample_data_other"],
                    sub_prefix,
                )
                render_field(
                    "mean_data_other",
                    section["mean_data_other"],
                    sub_prefix,
                )
                render_image_field(
                    "figure_other",
                    section["figure_other"],
                    sub_prefix,
                )


def _render_uncertainty_other(
    section: Evaluation,
    section_prefix: str,
) -> None:
    """
    Render the Uncertainty Metrics and Other block for the evaluation.

    :param section: The evaluation section containing the metrics.
    :type section: Evaluation
    :param section_prefix: The prefix for the section.
    :type section_prefix: str
    """
    section_divider()
    title_header("Uncertainty Metrics")
    col1, col2 = st.columns([1, 1])
    with col1:
        render_field(
            "uncertainty_metrics_method",
            section["uncertainty_metrics_method"],
            section_prefix,
        )
    with col2:
        render_field(
            "uncertainty_metrics_results",
            section["uncertainty_metrics_results"],
            section_prefix,
        )

    section_divider()
    title_header("Other")
    col1, col2 = st.columns([1, 1])
    with col1:
        render_field(
            "other_method",
            section["other_method"],
            section_prefix,
        )
    with col2:
        render_field(
            "other_results",
            section["other_results"],
            section_prefix,
        )


def _render_qualitative_block(
    section: Evaluation,
    section_prefix: str,
) -> None:
    """
    Render the Qualitative Metrics block for the evaluation.

    :param section: The evaluation section containing the metrics.
    :type section: Evaluation
    :param section_prefix: The prefix for the section.
    :type section_prefix: str
    """
    title_header_grey(TITLE_QUALITATIVE_EVALUATION)
    render_field(
        "evaluators_information",
        section["evaluators_information"],
        section_prefix,
    )

    tabs = st.tabs(
        ["Likert Scoring", "Turing Test", "Time Saving", "Other"],
    )
    with tabs[0]:
        title_header("Likert Scoring")
        col1, col2 = st.columns([1, 1])
        with col1:
            render_field(
                "likert_scoring_method",
                section["likert_scoring_method"],
                section_prefix,
            )
        with col2:
            render_field(
                "likert_scoring_results",
                section["likert_scoring_results"],
                section_prefix,
            )

    with tabs[1]:
        title_header("Turing Test")
        col1, col2 = st.columns([1, 1])
        with col1:
            render_field(
                "turing_test_method",
                section["turing_test_method"],
                section_prefix,
            )
        with col2:
            render_field(
                "turing_test_results",
                section["turing_test_results"],
                section_prefix,
            )

    with tabs[2]:
        title_header("Time Saving")
        col1, col2 = st.columns([1, 1])
        with col1:
            render_field(
                "time_saving_method",
                section["time_saving_method"],
                section_prefix,
            )
        with col2:
            render_field(
                "time_saving_results",
                section["time_saving_results"],
                section_prefix,
            )

    with tabs[3]:
        title_header("Other Evaluation")
        col1, col2 = st.columns([1, 1])
        with col1:
            render_field(
                "qualitative_other_method",
                section["qualitative_other_method"],
                section_prefix,
            )
        with col2:
            render_field(
                "qualitative_other_results",
                section["qualitative_other_results"],
                section_prefix,
            )

    section_divider()
    render_field(
        "explainability",
        section["explainability"],
        section_prefix,
    )
    render_field(
        "citation_details",
        section["citation_details"],
        section_prefix,
    )


def _render_quantitative_and_qualitative_tabs(
    section: Evaluation,
    section_prefix: str,
    current_task: str,
) -> None:
    """
    Render the quantitative and qualitative evaluation tabs by delegating
    to the previously defined helper functions.

    :param section: The evaluation section to render.
    :type section: Evaluation
    :param section_prefix: The prefix to use for the section fields.
    :type section_prefix: str
    :param current_task: The current task being evaluated.
    :type current_task: str
    """  # noqa: D205
    quant_qual_tabs = st.tabs(
        [
            TITLE_QUANTITATIVE_EVALUATION,
            TITLE_QUALITATIVE_EVALUATION,
        ],
    )
    current_task = st.session_state.get("task", "").strip().lower()
    with quant_qual_tabs[0]:
        title_header_grey(TITLE_QUANTITATIVE_EVALUATION)
        _render_image_similarity_metrics_block(
            section,
            section_prefix,
            current_task,
        )
        _render_image_dose_metrics_block(section, section_prefix, current_task)
        _render_segmentation_geometric_block(
            section, section_prefix, current_task,
        )
        _render_segmentation_dose_block(section, section_prefix, current_task)
        _render_iov_block(section, section_prefix, current_task)
        _render_dose_prediction_dose_block(
            section, section_prefix, current_task,
        )
        _render_other_metrics(section, section_prefix, current_task)
        _render_uncertainty_other(section, section_prefix)

    with quant_qual_tabs[1]:
        _render_qualitative_block(section, section_prefix)


def _render_one_evaluation_form(
    form_name: str,
    eval_schema: Evaluation,
    current_task: str,
) -> None:
    """
    Render one evaluation form inside an expander, with delete button.

    :param form_name: The name of the evaluation form.
    :type form_name: str
    :param eval_schema: The evaluation schema to use for rendering.
    :type eval_schema: Evaluation
    :param task: The current task being evaluated.
    :type task: str
    """
    current_task = st.session_state.get("task", "").strip().lower()
    section_prefix = f"evaluation_{form_name.replace(' ', '_')}"
    with st.expander(f"{form_name}", expanded=False):
        _render_header_and_evaluated_by(eval_schema, section_prefix)
        _render_general_info(eval_schema, section_prefix)
        _render_technical_characteristics(eval_schema, section_prefix)
        _render_dose_prediction_eval(eval_schema, section_prefix, current_task)
        _render_reference_and_demographics(eval_schema, section_prefix, current_task)  # noqa: E501
        _render_quantitative_and_qualitative_tabs(
            eval_schema,
            section_prefix,
            current_task,
        )

        col1, col2 = st.columns([0.2, 0.8])  # noqa: RUF059
        with col1:
            if st.button("Delete", key=f"delete_eval_{form_name}"):
                st.session_state["_to_delete_eval_form"] = form_name


def _render_navigation() -> None:
    """Render the navigation buttons."""
    col1, _, _, _, col5 = st.columns([1.5, 2, 4.3, 2, 1.1])
    with col1:
        if st.button("Previous"):
            from app.ui.screens.sections.training_data import (  # noqa: PLC0415
                training_data_render,
            )

            st.session_state.runpage = training_data_render
            st.rerun()
    with col5:
        if st.button("Next"):
            from app.ui.screens.sections.other_considerations import (  # noqa: PLC0415
                other_considerations_render,
            )

            st.session_state.runpage = other_considerations_render
            st.rerun()


def evaluation_data_mrc_render() -> None:
    """Evaluation data, methodology, and results / commissioning page."""
    from app.ui.components.sidebar import sidebar_render  # noqa: PLC0415

    sidebar_render()

    schema_any: dict[str, Any] = schema_loader.get_model_card_schema()
    eval_schema = cast(
        "Evaluation",
        schema_any["evaluation_data_methodology_results_commisioning"],
    )

    title(TITLE)
    subtitle(SUBTITLE)

    current_task = st.session_state.get("task", "Image-to-Image translation")

    if "evaluation_forms" not in st.session_state:
        st.session_state.evaluation_forms = []

    with st.expander("Add New Evaluation Form"):
        new_form_name = st.text_input("Evaluation name", key="new_eval_name")
        if st.button("Add Evaluation Form"):
            if new_form_name:
                if new_form_name not in st.session_state.evaluation_forms:
                    st.session_state.evaluation_forms.append(new_form_name)
                    st.success(f"Added evaluation form: {new_form_name}")
                    st.rerun()
                else:
                    st.warning(WARNING_EVAL_EXISTS)
            else:
                st.warning("Please enter a name for the evaluation form.")

    # Render forms
    for form_name in list(st.session_state.evaluation_forms):
        _render_one_evaluation_form(form_name, eval_schema, current_task)

    # Handle deletion if requested
    form_to_delete = st.session_state.pop("_to_delete_eval_form", None)
    if form_to_delete:
        st.session_state.evaluation_forms.remove(form_to_delete)
        prefix = f"evaluation_{form_to_delete.replace(' ', '_')}_"
        for key in list(st.session_state.keys()):
            if isinstance(key, str) and key.startswith(prefix):
                del st.session_state[key]
        st.rerun()

    # Navigation (unchanged behavior)
    st.markdown("<br>", unsafe_allow_html=True)
    _render_navigation()
