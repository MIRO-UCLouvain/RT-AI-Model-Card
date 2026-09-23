"""Module to select the task for the Model Card (card chooser)."""

from __future__ import annotations

import streamlit as st

from app.ui.components.back_home import render_back_to_home

TASKS: tuple[str, ...] = (
    "Image-to-Image translation",
    "Segmentation",
    "Dose prediction",
    "Other",
)

# Cards are plain Streamlit buttons laid out in columns: columns span the
# full width by construction, unlike the radio widget, whose intrinsic width
# can't be overridden from CSS.
_STYLES = """
<style>
/* ── Heading ─────────────────────────────────────────────────────────── */
.task-heading{
  text-align: center;
  margin: clamp(1.5rem, 3vw, 2.5rem) auto clamp(1.75rem, 3.5vw, 2.75rem);
}
.task-heading h2{
  margin: 0 0 .5rem;
  color: var(--brand-600, #184197);
  font-size: clamp(26px, 2.6vw, 34px);
  font-weight: 800;
  letter-spacing: -.015em;
}
.task-heading p{
  margin: 0;
  color: #475569;
  font-size: clamp(15px, 1.1vw, 17px);
  text-align: center;
}

/* ── Task cards ──────────────────────────────────────────────────────── */
[class*="st-key-task_card_"] button{
  min-height: 6rem;
  padding: 1.1rem .9rem;
  border-radius: 12px;
  border: 1.5px solid #d7e0f0;
  background: #ffffff;
  color: #1e293b;
  font-size: clamp(15px, 1.05vw, 17px);
  font-weight: 600;
  line-height: 1.35;
  white-space: normal;
  transition: border-color .15s ease, background .15s ease,
              box-shadow .15s ease, transform .1s ease;
}
[class*="st-key-task_card_"] button:hover{
  border-color: #184197;
  background: #f5f8ff;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(24, 65, 151, .10);
}
/* Selected card: outlined in the brand blue, so it reads as chosen without
   competing with the solid blue call to action below. */
[class*="st-key-task_card_"] button[data-testid="stBaseButton-primary"]{
  background: #eaf1ff !important;
  border: 2px solid #184197 !important;
  color: #184197 !important;
  box-shadow: 0 6px 18px rgba(24, 65, 151, .14);
}

/* ── Continue: outlined call to action ───────────────────────────────── */
.st-key-task_continue{ margin-top: clamp(2rem, 4vw, 3rem); }
.st-key-task_continue button{
  background: #ffffff !important;
  border: 2px solid #0553D1 !important;
  color: #0553D1 !important;
  font-size: clamp(16px, 1.15vw, 18px);
  font-weight: 700;
  min-height: 3.1rem;
  border-radius: 10px;
  transition: background .15s ease, border-color .15s ease, color .15s ease;
}
.st-key-task_continue button:hover{
  background: #eaf1ff !important;
  border-color: #184197 !important;
  color: #184197 !important;
}

/* ── Footer area ─────────────────────────────────────────────────────── */
.task-divider{
  margin: clamp(2.5rem, 5vw, 4rem) auto clamp(1.25rem, 2.5vw, 2rem);
  border: 0;
  border-top: 1px solid rgba(24, 65, 151, .12);
}
</style>
"""


def _render_cards() -> None:
    """Render one selectable card per task."""
    cols = st.columns(len(TASKS), gap="medium")
    current: str | None = st.session_state.get("task_temp")

    for col, task in zip(cols, TASKS, strict=True):
        with col:
            picked = st.button(
                task,
                key=f"task_card_{task.replace(' ', '_').lower()}",
                use_container_width=True,
                type="primary" if task == current else "secondary",
            )
        if picked:
            st.session_state["task_temp"] = task
            st.rerun()


def task_selector_page() -> None:
    """Render the task selector page."""
    st.markdown(_STYLES, unsafe_allow_html=True)

    st.markdown(
        '<div class="task-heading">'
        "<h2>Select the task for your Model Card</h2>"
        "<p>Pick the task your model performs.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    if "task" not in st.session_state:
        st.session_state.setdefault("task_temp", TASKS[0])
        _render_cards()

        _, col_continue, _ = st.columns([1, 2, 1])
        with col_continue:
            if st.button(
                "Continue →",
                key="task_continue",
                type="primary",
                use_container_width=True,
            ):
                st.session_state["task"] = st.session_state["task_temp"]
                # Lazy import to avoid circular import
                from app.ui.screens.sections.model_card_info import (  # noqa: PLC0415
                    model_card_info_render,
                )

                st.session_state.runpage = model_card_info_render
                st.rerun()
    else:
        st.success(f"Task already selected: **{st.session_state['task']}**")

    st.markdown('<hr class="task-divider" />', unsafe_allow_html=True)
    _, col_back, _ = st.columns([2, 1, 2])
    with col_back:
        render_back_to_home(key="task_back_home")
