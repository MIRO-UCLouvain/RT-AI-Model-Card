"""Warnings page for the Model Cards Writing Tool."""


import streamlit as st

from app.services import schema_loader
from app.services.validation import validate_required_fields

model_card_schema = schema_loader.get_model_card_schema()

SECTION_NAMES = {
    "Card Metadata": ["card_metadata"],
    "Model Basic Information": ["model_basic_information"],
    "Technical Specifications": [
        "technical_specifications",
        "learning_architecture",
    ],
    "Training data, methodology, and information": [
        "training_data",
    ],
    "Evaluation data, methodology, and results / commissioning": [
        "evaluation_data_methodology_results_commisioning",
        "qualitative_evaluation",
    ],
}

def warnings_render() -> None:
    """Render warnings for missing required fields in the model card."""
    from app.ui.components.sidebar import sidebar_render  # noqa: PLC0415

    sidebar_render()

    task: str = st.session_state.get("task", "Image-to-Image translation")

    missing_required: list[tuple[str, str]] = validate_required_fields(
        model_card_schema,
        current_task=task,
    )

    grouped_missing: dict[str, list[str]] = {}
    for section, label in missing_required:
        if section not in grouped_missing:
            grouped_missing[section] = []
        grouped_missing[section].append(label)

    if not grouped_missing:
        return

    section_label_map: dict[str, str] = {}
    for display_name, internal_keys in SECTION_NAMES.items():
        for key in internal_keys:
            section_label_map[key] = display_name

    display_grouped: dict[str, list[str]] = {}
    for section_key, labels in grouped_missing.items():
        section_title = section_label_map.get(section_key)
        if section_title:
            display_grouped.setdefault(section_title, []).extend(labels)

    for section_title, labels in display_grouped.items():
        st.info(f"Section: {section_title}")
        st.warning(f"Missing required fields: {', '.join(labels)}")
