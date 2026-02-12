"""Feedback / contact form screen at ?view=contact."""

from __future__ import annotations

import re

import streamlit as st

from app.client.model_cards import BackendError, submit_feedback

_TOPICS = [
    "General feedback",
    "Bug report",
    "Feature request",
    "UX / interface",
    "Login / account",
    "Model basic information",
    "Clinical problem",
    "Intended use",
    "Training data",
    "Validation data",
    "Model performance",
    "Limitations",
    "Ethical considerations",
    "Publication workflow",
    "PDF export",
    "Other",
]

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def feedback_page() -> None:
    """Render the feedback / contact form."""
    st.markdown("<br>", unsafe_allow_html=True)
    _, col, _ = st.columns([0.6, 2, 0.6])
    with col:
        with st.container(border=True):
            st.markdown(
                '<p style="font-size:1.5rem;font-weight:700;margin:0 0 4px;'
                'color:var(--ink,#1e293b);">Contact us</p>'
                '<p style="color:var(--muted,#64748b);font-size:0.9rem;'
                'margin:0 0 20px;">Send feedback, report a bug, or request a feature.</p>',
                unsafe_allow_html=True,
            )

            # Pre-fill email if logged in
            default_email = st.session_state.get("auth_email") or ""

            with st.form("form_feedback", clear_on_submit=True):
                email = st.text_input(
                    "Email address *",
                    value=default_email,
                    placeholder="you@example.com",
                    key="feedback_email",
                )
                topic = st.selectbox(
                    "Topic *",
                    options=_TOPICS,
                    index=0,
                    key="feedback_topic",
                )
                subject = st.text_input(
                    "Subject *",
                    placeholder="Brief description of your feedback",
                    key="feedback_subject",
                )
                message = st.text_area(
                    "Message *",
                    placeholder="Tell us more…",
                    height=160,
                    key="feedback_message",
                )

                submitted = st.form_submit_button(
                    "Send feedback",
                    use_container_width=True,
                )

            if submitted:
                # ── Validation ────────────────────────────────────────
                errors: list[str] = []
                email_val = (email or "").strip()
                subject_val = (subject or "").strip()
                message_val = (message or "").strip()
                topic_val = topic or ""

                if not email_val:
                    errors.append("Email address is required.")
                elif not _EMAIL_RE.match(email_val):
                    errors.append("Please enter a valid email address.")

                if not topic_val:
                    errors.append("Please select a topic.")

                if not subject_val:
                    errors.append("Subject is required.")

                if not message_val:
                    errors.append("Message is required.")
                elif len(message_val) < 10:
                    errors.append("Message must be at least 10 characters.")

                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    # Capture current page context
                    page_context = st.session_state.get("_feedback_origin", "")

                    token = st.session_state.get("auth_token") or ""
                    try:
                        result = submit_feedback(
                            email=email_val,
                            topic=topic_val,
                            subject=subject_val,
                            message=message_val,
                            page_context=page_context,
                            token=token,
                        )
                        st.success(result.get("message", "Thanks — your feedback has been sent."))
                    except BackendError as exc:
                        st.error(f"Could not send feedback: {exc}")

    st.markdown("---")
    _, col_back, _ = st.columns([1, 2, 1])
    with col_back:
        if st.button(
            "← Back",
            key="feedback_back",
            use_container_width=True,
        ):
            st.query_params["view"] = "home"
            st.rerun()
