"""Technical specifications page for the Model Cards Writing Tool."""

from __future__ import annotations

from typing import Any, TypedDict, cast

import streamlit as st

from app.services import schema_loader
from app.ui.forms.render import FieldProps, render_field, render_image_field
from app.ui.utils.typography import (
    light_header_italics,
    section_divider,
    subtitle,
    title,
    title_header,
)

TITLE = "Technical Specifications"
SUBTITLE = (
    "(i.e. model pipeline, learning architecture, software and hardware)"
)
TITLE_SUBSECTION_MODEL_OVERVIEW = "1. Model overview"
TITLE_SUBSECTION_MODEL_OVERVIEW_PIPELINE = "Model pipeline"
TITLE_SUBSECTION_MODEL_OVERVIEW_INPUTS = "Model inputs"
TITLE_SUBSECTION_MODEL_OVERVIEW_OUTPUTS = "Model outputs"
TITLE_SUBSECTION_LA = "2. Learning Architecture"
TITLE_SUBSECTION_HW_SW = "3. Hardware & Software"
LEARNING_ARCHITECTURE_INFO = (
    "If several models are used (e.g. cascade, cycle, tree,...), "
    "repeat this section for each of them."
)
LEARNING_ARCHITECTURE_WARNING = (
    "At least one learning architecture is required."
    " Please add one."
)

SECTION_TECH = "technical_specifications"
SECTION_LA = "learning_architecture"
SECTION_HW_SW = "hw_and_sw"


class ModelOverview(TypedDict, total=False):
    """
    TypedDict describing the fields for the 'Model Overview'.

    :param TypedDict: The base class for TypedDicts
    :type TypedDict: type
    :param total: If True, all fields are required, defaults to False
    :type total: bool, optional
    """

    model_pipeline_summary: FieldProps
    model_pipeline_figure: FieldProps
    model_inputs: FieldProps
    additional_information_model_inputs: FieldProps
    model_outputs: FieldProps
    additional_information_model_outputs: FieldProps
    pre_processing: FieldProps
    post_processing: FieldProps


class LearningArchitecture(TypedDict, total=False):
    """
    TypedDict describing the fields for each 'Learning Architecture'.

    :param TypedDict: The base class for TypedDicts
    :type TypedDict: type
    :param total: If True, all fields are required, defaults to False
    :type total: bool, optional
    """

    total_number_trainable_parameters: FieldProps
    number_of_inputs: FieldProps
    input_content: FieldProps
    additional_information_input_content: FieldProps
    input_format: FieldProps
    input_size: FieldProps
    number_of_outputs: FieldProps
    output_content: FieldProps
    additional_information_output_content: FieldProps
    output_format: FieldProps
    output_size: FieldProps
    loss_function: FieldProps
    batch_size: FieldProps
    regularisation: FieldProps
    architecture_figure: FieldProps
    uncertainty_quantification_techniques: FieldProps
    explainability_techniques: FieldProps
    additional_information_ts: FieldProps
    citation_details_ts: FieldProps


class HardwareSoftware(TypedDict, total=False):
    """
    TypedDict describing the fields for the 'Hardware and Software'.

    :param TypedDict: The base class for TypedDicts
    :type TypedDict: type
    :param total: If True, all fields are required, defaults to False
    :type total: bool, optional
    """

    libraries_and_dependencies: FieldProps
    hardware_recommended: FieldProps
    inference_time_for_recommended_hw: FieldProps
    installation_getting_started: FieldProps
    environmental_impact: FieldProps


def _render_model_overview(mo_section: ModelOverview) -> None:
    title_header(TITLE_SUBSECTION_MODEL_OVERVIEW, size="1.35rem")
    title_header(TITLE_SUBSECTION_MODEL_OVERVIEW_PIPELINE)

    render_field(
        "model_pipeline_summary",
        mo_section["model_pipeline_summary"],
        SECTION_TECH,
    )
    render_image_field(
        "model_pipeline_figure",
        mo_section["model_pipeline_figure"],
        SECTION_TECH,
    )

    section_divider()

    title_header(TITLE_SUBSECTION_MODEL_OVERVIEW_INPUTS, size="1.25rem")
    render_field(
        "model_inputs",
        mo_section["model_inputs"],
        SECTION_TECH,
    )
    render_field(
        "additional_information_model_inputs",
        mo_section["additional_information_model_inputs"],
        SECTION_TECH,
    )

    section_divider()

    title_header(TITLE_SUBSECTION_MODEL_OVERVIEW_OUTPUTS, size="1.25rem")
    render_field(
        "model_outputs",
        mo_section["model_outputs"],
        SECTION_TECH,
    )
    render_field(
        "additional_information_model_outputs",
        mo_section["additional_information_model_outputs"],
        SECTION_TECH,
    )

    section_divider()
    col1, col2 = st.columns([1, 1])
    with col1:
        render_field(
            "pre_processing",
            mo_section["pre_processing"],
            SECTION_TECH,
        )
    with col2:
        render_field(
            "post_processing",
            mo_section["post_processing"],
            SECTION_TECH,
        )


def _render_learning_architectures(
    la_section: LearningArchitecture,
) -> None:
    title_header(TITLE_SUBSECTION_LA, size="1.35rem")
    light_header_italics(LEARNING_ARCHITECTURE_INFO)

    with st.container():
        col1, col2, col3 = st.columns([1.8, 2, 1.2])

        with col1:
            st.markdown(
                "<div style='margin-top: 6px;'>",
                unsafe_allow_html=True,
            )
            st.button("Add Learning Architecture", key="add_learning_arch")
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            forms: list[str] = [
                str(k)
                for k in st.session_state.learning_architecture_forms
            ]
            st.markdown(
                "<div style='height: 1px; margin-top: -28px;'></div>",
                unsafe_allow_html=True,
            )
            delete_index: str = st.selectbox(
                label=".",
                options=forms,
                index=0,
                key="learning_architecture_delete_select_clean",
                label_visibility="collapsed",
            )

        with col3:
            st.markdown(
                "<div style='margin-top: 6px;'>",
                unsafe_allow_html=True,
            )
            if st.button("Delete", key="delete_learning_arch_clean"):
                if not delete_index:
                    st.warning("Please select a model to delete.")
                else:
                    selected_key: str = str(delete_index)
                    selected_index = int(selected_key.split()[-1])

                    st.session_state.learning_architecture_forms.pop(
                        selected_key,
                    )

                    keys_to_remove = [
                        k
                        for k in list(st.session_state.keys())
                        if isinstance(k, str) and k.startswith(
                            f"learning_architecture_{selected_index}_",
                        )
                    ]
                    for k in keys_to_remove:
                        del st.session_state[k]

                    # Reindex state keys to close gaps (preserved behavior)
                    for i in range(selected_index + 1, len(forms) + 1):
                        old_prefix = f"learning_architecture_{i}_"
                        new_prefix = f"learning_architecture_{i - 1}_"
                        for k in map(str, st.session_state.keys()):
                            if isinstance(k, str) and k.startswith(old_prefix):
                                new_key = str(k).replace(
                                    old_prefix,
                                    new_prefix,
                                )
                                st.session_state[new_key] = (
                                    st.session_state.pop(k)
                                )

                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.get("add_learning_arch", False):
            n = len(st.session_state.learning_architecture_forms)
            st.session_state.learning_architecture_forms[
                f"Learning Architecture {n + 1}"
            ] = {}
            st.rerun()

    tab_labels = list(st.session_state.learning_architecture_forms.keys())
    if not tab_labels:
        st.warning(LEARNING_ARCHITECTURE_WARNING)
        return

    tabs = st.tabs(tab_labels)
    for i, tab in enumerate(tabs):
        with tab:
            _render_learning_architecture_tab(la_section, index=i)


def _render_learning_architecture_tab(
    la_section: LearningArchitecture,
    *,
    index: int,
) -> None:
    prefix = f"learning_architecture_{index}"

    col1, col2 = st.columns([2, 1])
    with col1:
        render_field(
            "total_number_trainable_parameters",
            la_section["total_number_trainable_parameters"],
            prefix,
        )
    with col2:
        render_field(
            "number_of_inputs",
            la_section["number_of_inputs"],
            prefix,
        )

    render_field(
        "input_content",
        la_section["input_content"],
        prefix,
    )
    render_field(
        "additional_information_input_content",
        la_section["additional_information_input_content"],
        prefix,
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        render_field(
            "input_format",
            la_section["input_format"],
            prefix,
        )
    with col2:
        render_field(
            "input_size",
            la_section["input_size"],
            prefix,
        )

    render_field(
        "number_of_outputs",
        la_section["number_of_outputs"],
        prefix,
    )
    render_field(
        "output_content",
        la_section["output_content"],
        prefix,
    )
    render_field(
        "additional_information_output_content",
        la_section["additional_information_output_content"],
        prefix,
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        render_field(
            "output_format",
            la_section["output_format"],
            prefix,
        )
    with col2:
        render_field(
            "output_size",
            la_section["output_size"],
            prefix,
        )

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        render_field(
            "loss_function",
            la_section["loss_function"],
            prefix,
        )
    with col2:
        render_field(
            "batch_size",
            la_section["batch_size"],
            prefix,
        )
    with col3:
        render_field(
            "regularisation",
            la_section["regularisation"],
            prefix,
        )

    render_image_field(
        "architecture_figure",
        la_section["architecture_figure"],
        prefix,
    )

    render_field(
        "uncertainty_quantification_techniques",
        la_section["uncertainty_quantification_techniques"],
        prefix,
    )
    render_field(
        "explainability_techniques",
        la_section["explainability_techniques"],
        prefix,
    )
    render_field(
        "additional_information_ts",
        la_section["additional_information_ts"],
        prefix,
    )
    render_field(
        "citation_details_ts",
        la_section["citation_details_ts"],
        prefix,
    )


def _render_hw_sw(hw_section: HardwareSoftware) -> None:
    title_header(TITLE_SUBSECTION_HW_SW, size="1.35rem")

    render_field(
        "libraries_and_dependencies",
        hw_section["libraries_and_dependencies"],
        SECTION_HW_SW,
    )

    col1, col2 = st.columns(2)
    with col1:
        render_field(
            "hardware_recommended",
            hw_section["hardware_recommended"],
            SECTION_HW_SW,
        )
    with col2:
        render_field(
            "inference_time_for_recommended_hw",
            hw_section["inference_time_for_recommended_hw"],
            SECTION_HW_SW,
        )

    col1, col2 = st.columns(2)
    with col1:
        render_field(
            "installation_getting_started",
            hw_section["installation_getting_started"],
            SECTION_HW_SW,
        )
    with col2:
        render_field(
            "environmental_impact",
            hw_section["environmental_impact"],
            SECTION_HW_SW,
        )


def _render_navigation() -> None:
    """Render the navigation buttons."""
    st.markdown("<br>", unsafe_allow_html=True)
    col1, _, _, _, col5 = st.columns([1.5, 2, 4.3, 2, 1.1])

    with col1:
        if st.button("Previous"):
            from app.ui.screens.sections.model_basic_information import (  # noqa: PLC0415
                model_basic_information_render,
            )

            st.session_state.runpage = model_basic_information_render
            st.rerun()

    with col5:
        if st.button("Next"):
            from app.ui.screens.sections.training_data import (  # noqa: PLC0415
                training_data_render,
            )

            st.session_state.runpage = training_data_render
            st.rerun()


def technical_specifications_render() -> None:
    """Render the Technical Specifications page."""
    from app.ui.components.sidebar import sidebar_render  # noqa: PLC0415

    sidebar_render()
    model_card_schema: dict[str, Any] = schema_loader.get_model_card_schema()

    ts_section = cast("ModelOverview", model_card_schema[SECTION_TECH])
    la_section = cast("LearningArchitecture", model_card_schema[SECTION_LA])
    hw_section = cast("HardwareSoftware", model_card_schema[SECTION_HW_SW])

    title(TITLE)
    subtitle(SUBTITLE)

    if "learning_architecture_forms" not in st.session_state:
        st.session_state.learning_architecture_forms = {
            "Learning Architecture 1": {},
        }
    if "selected_learning_arch_to_delete" not in st.session_state:
        st.session_state.selected_learning_arch_to_delete = None

    _render_model_overview(ts_section)
    section_divider()
    _render_learning_architectures(la_section)
    section_divider()
    _render_hw_sw(hw_section)
    _render_navigation()
