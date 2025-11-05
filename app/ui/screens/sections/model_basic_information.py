"""Model Basic Information page for the Model Cards Writing Tool."""

from __future__ import annotations

from typing import Any, TypedDict, cast

import streamlit as st

from app.services import schema_loader
from app.ui.forms.render import FieldProps, render_field
from app.ui.utils.typography import (
    light_header_italics,
    section_divider,
    subtitle,
    title,
    title_header,
)

TITLE = "Model Basic Information"
SUBTITLE = "with the main information to use the model"
SECTION_PREFIX = "model_basic_information"

VERSIONING_HEADER = "Versioning"
VERSIONING_INFO = (
    "Note that any change in an existing model is considered as a new version"
    " and thus a new model card associated with it should be filled in."
)


class ModelBasicInformation(TypedDict, total=False):
    """
    TypedDict for the 'Model Basic Information' section.

    :param TypedDict: The base class for TypedDicts.
    :type TypedDict: type
    :param total: If True, all fields are required, defaults to False
    :type total: bool, optional
    """
    name: FieldProps
    creation_date: FieldProps

    version_number: FieldProps
    version_changes: FieldProps
    doi: FieldProps

    model_scope_summary: FieldProps
    model_scope_anatomical_site: FieldProps

    clearance_type: FieldProps
    clearance_approved_by_name: FieldProps
    clearance_approved_by_institution: FieldProps
    clearance_approved_by_contact_email: FieldProps
    clearance_additional_information: FieldProps

    intended_users: FieldProps
    observed_limitations: FieldProps
    potential_limitations: FieldProps
    type_of_learning_architecture: FieldProps

    developed_by_name: FieldProps
    developed_by_institution: FieldProps
    developed_by_email: FieldProps
    conflict_of_interest: FieldProps
    software_license: FieldProps
    code_source: FieldProps
    model_source: FieldProps
    citation_details: FieldProps
    url_info: FieldProps


def _render_name_and_date(section: ModelBasicInformation) -> None:
    if "name" in section and "creation_date" in section:
        col1, col2 = st.columns(2)
        with col1:
            render_field(
                "name",
                section["name"],
                SECTION_PREFIX,
            )
        with col2:
            render_field(
                "creation_date",
                section["creation_date"],
                SECTION_PREFIX,
            )


def _render_versioning(section: ModelBasicInformation) -> None:
    section_divider()
    title_header(VERSIONING_HEADER)
    light_header_italics(VERSIONING_INFO)

    if "version_number" in section and "version_changes" in section:
        col1, col2 = st.columns([1, 3])
        with col1:
            section["version_number"].setdefault("placeholder", "MM.mm.bbbb")
            render_field(
                "version_number",
                section["version_number"],
                SECTION_PREFIX,
            )
        with col2:
            vc_props = cast(
                "FieldProps",
                {
                    **section["version_changes"],
                    "placeholder": "NA if Not Applicable",
                },
            )
            render_field(
                "version_changes",
                vc_props,
                SECTION_PREFIX,
            )

    section_divider()
    if "doi" in section:
        render_field(
            "doi",
            section["doi"],
            SECTION_PREFIX,
        )


def _render_model_scope(section: ModelBasicInformation) -> None:
    section_divider()
    title_header("Model scope")

    if (
        "model_scope_summary" in section
        and "model_scope_anatomical_site" in section
    ):
        col1, col2 = st.columns([2, 1])
        with col1:
            render_field(
                "model_scope_summary",
                section["model_scope_summary"],
                SECTION_PREFIX,
            )
        with col2:
            render_field(
                "model_scope_anatomical_site",
                section["model_scope_anatomical_site"],
                SECTION_PREFIX,
            )
    section_divider()


def _render_clearance(section: ModelBasicInformation) -> None:
    title_header("Clearance")

    if "clearance_type" in section:
        render_field(
            "clearance_type",
            section["clearance_type"],
            SECTION_PREFIX,
        )

    if all(
        k in section
        for k in [
            "clearance_approved_by_name",
            "clearance_approved_by_institution",
            "clearance_approved_by_contact_email",
        ]
    ):
        title_header("Approved by", "1rem")
        col1, col2, col3 = st.columns([1, 1.5, 1.5])
        with col1:
            render_field(
                "clearance_approved_by_name",
                section["clearance_approved_by_name"],
                SECTION_PREFIX,
            )
        with col2:
            render_field(
                "clearance_approved_by_institution",
                section["clearance_approved_by_institution"],
                SECTION_PREFIX,
            )
        with col3:
            render_field(
                "clearance_approved_by_contact_email",
                section["clearance_approved_by_contact_email"],
                SECTION_PREFIX,
            )

    if "clearance_additional_information" in section:
        render_field(
            "clearance_additional_information",
            section["clearance_additional_information"],
            SECTION_PREFIX,
        )

    section_divider()


def _render_limitations_fields(section: ModelBasicInformation) -> None:
    render_field(
        "intended_users",
        section["intended_users"],
        SECTION_PREFIX,
    )
    render_field(
        "observed_limitations",
        section["observed_limitations"],
        SECTION_PREFIX,
    )
    render_field(
        "potential_limitations",
        section["potential_limitations"],
        SECTION_PREFIX,
    )
    render_field(
        "type_of_learning_architecture",
        section["type_of_learning_architecture"],
        SECTION_PREFIX,
    )
    section_divider()


def _render_developed_by_and_sources(section: ModelBasicInformation) -> None:
    title_header("Developed by")
    col1, col2, col3 = st.columns([1, 1.5, 1.5])
    with col1:
        render_field(
            "developed_by_name",
            section["developed_by_name"],
            SECTION_PREFIX,
        )
    with col2:
        render_field(
            "developed_by_institution",
            section["developed_by_institution"],
            SECTION_PREFIX,
        )
    with col3:
        render_field(
            "developed_by_email",
            section["developed_by_email"],
            SECTION_PREFIX,
        )

    section_divider()

    coi_props = cast(
        "FieldProps",
        {
            **section["conflict_of_interest"],
            "placeholder": "NA if Not Applicable",
        },
    )
    render_field(
        "conflict_of_interest",
        coi_props,
        SECTION_PREFIX,
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        render_field(
            "software_license",
            section["software_license"],
            SECTION_PREFIX,
        )
    with col2:
        render_field(
            "code_source",
            section["code_source"],
            SECTION_PREFIX,
        )
    with col3:
        render_field("model_source", section["model_source"], SECTION_PREFIX)

    col1, col2 = st.columns([1, 1])
    with col1:
        render_field(
            "citation_details",
            section["citation_details"],
            SECTION_PREFIX,
        )
    with col2:
        render_field(
            "url_info",
            section["url_info"],
            SECTION_PREFIX,
        )

    st.markdown("<br>", unsafe_allow_html=True)


def _render_navigation() -> None:
    """Render the navigation buttons."""
    col1, _, _, _, col5 = st.columns([1.5, 2, 4.3, 2, 1.1])

    with col1:
        if st.button("Previous"):
            from app.ui.screens.sections.card_metadata import (  # noqa: PLC0415
                card_metadata_render,
            )

            st.session_state.runpage = card_metadata_render
            st.rerun()

    with col5:
        if st.button("Next"):
            from app.ui.screens.sections.technical_specifications import (  # noqa: PLC0415
                technical_specifications_render,
            )

            st.session_state.runpage = technical_specifications_render
            st.rerun()


def model_basic_information_render() -> None:
    """Render the Model Basic Information page."""
    from app.ui.components.sidebar import sidebar_render  # noqa: PLC0415

    sidebar_render()

    # get_model_card_schema() returns a big dict; we only need our section.
    schema_any: dict[str, Any] = schema_loader.get_model_card_schema()
    section = cast("ModelBasicInformation", schema_any.get(SECTION_PREFIX, {}))

    title(TITLE)
    subtitle(SUBTITLE)

    _render_name_and_date(section)
    _render_versioning(section)
    _render_model_scope(section)
    _render_clearance(section)
    _render_limitations_fields(section)
    _render_developed_by_and_sources(section)
    _render_navigation()
