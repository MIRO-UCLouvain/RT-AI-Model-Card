"""Module for template registry."""
from pathlib import Path

TEMPLATES_DIR = Path("app/core/templates/md")

SECTION_REGISTRY = {
    "card_metadata": {
        "prefix": "card_metadata_",
        "template": "card_metadata.md.j2",
    },
    "model_basic_information": {
        "prefix": "model_basic_information_",
        "template": "model_basic_information.md.j2",
    },
    "technical_specifications": {
        "prefix": "technical_specifications_",
        "template": "technical_specifications.md.j2",
    },
    "training_data": {
        "prefix": "training_data_",
        "template": "training.md.j2",
    },
    "evaluations": {
    "prefix": "evaluations_",
    "template": "evaluations.md.j2",
    },
    "other_considerations": {
        "prefix": "other_considerations_",
        "template": "other_considerations.md.j2",
    },
}
