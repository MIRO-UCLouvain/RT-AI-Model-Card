"""Register screen — centered form at ?view=register."""

from __future__ import annotations

import streamlit as st

from app.client.model_cards import BackendError, login, register
from app.ui.utils.auth import save_auth


def register_page() -> None:
    """Render the centered registration form."""
    # Same pattern as login_page: collect auth data inside the container,
    # then call save_auth() outside to avoid components.html rendering artifacts.
    _auth_result: tuple | None = None

    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([0.6, 2, 0.6])
    with col:
        with st.container(border=True):
            st.header("Create Account")

            with st.form("form_register_page"):
                first_name = st.text_input("First Name", key="reg_page_first_name")
                last_name = st.text_input("Last Name", key="reg_page_last_name")
                email = st.text_input("Email", key="reg_page_email")
                password = st.text_input(
                    "Password (min 8 chars)",
                    type="password",
                    key="reg_page_pass",
                )
                submitted = st.form_submit_button(
                    "Create Account", use_container_width=True
                )

            if submitted:
                if not first_name or not last_name or not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    try:
                        register(
                            email.strip(),
                            password,
                            first_name.strip(),
                            last_name.strip(),
                        )
                        # Auto-login after registration
                        result = login(email.strip(), password)
                        _auth_result = (
                            result["access_token"],
                            email.strip(),
                            first_name.strip(),
                            last_name.strip(),
                        )
                        st.query_params["view"] = "home"
                    except BackendError as exc:
                        st.error(str(exc))

            st.markdown(
                "<div style='text-align:center; padding: 16px 0 28px 0'>Already have an account? <a href='?view=login'>Sign in</a></div>",
                unsafe_allow_html=True,
            )

    # Inject auth cookies outside any container — prevents rendering artifacts.
    if _auth_result:
        save_auth(_auth_result[0], _auth_result[1], first_name=_auth_result[2], last_name=_auth_result[3])
        st.rerun()

    st.markdown("---")
    _, col_back, _ = st.columns([1, 2, 1])
    with col_back:
        if st.button("← Back to Main Page", key="register_back_home", use_container_width=True):
            st.query_params["view"] = "home"
            st.rerun()
