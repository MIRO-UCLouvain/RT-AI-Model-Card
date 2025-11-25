"""Profile screen — user details and logout at ?view=profile."""

from __future__ import annotations

import streamlit as st

from app.ui.utils.auth import clear_auth


def profile_page() -> None:
    """Render the user profile page with account details and logout."""
    if not st.session_state.get("auth_token"):
        st.warning("You must be logged in to view your profile.")
        st.markdown("[Login](?view=login)", unsafe_allow_html=True)
        return

    email: str = st.session_state.get("auth_email", "")
    username: str = email.split("@")[0] if email else ""

    st.header("My Profile")
    st.markdown(f"**Name:** {username}")
    st.markdown(f"**Email:** {email}")

    st.markdown("---")
    if st.button("Logout", type="primary", use_container_width=True):
        clear_auth()
        st.query_params["view"] = "home"
        st.rerun()

    st.markdown("---")
    col_back, col_issue = st.columns(2)
    with col_back:
        if st.button("← Back to Main Page", key="profile_back_home", use_container_width=True):
            st.query_params["view"] = "home"
            st.rerun()
    with col_issue:
        st.link_button(
            "Open an Issue ↗",
            "https://github.com/MIRO-UCLouvain/RT-Model-Card/issues",
            use_container_width=True,
        )
