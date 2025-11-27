"""Login screen — centered form at ?view=login."""

from __future__ import annotations

import streamlit as st

from app.client.model_cards import BackendError, get_me, login
from app.ui.utils.auth import save_auth


def login_page() -> None:
    """Render the centered login form."""
    # Holds (token, email, first_name, last_name) on a successful login attempt.
    # save_auth() is called AFTER the container closes to avoid rendering the
    # components.html iframe inside a nested column/container (which can cause
    # the form to appear duplicated before st.rerun() takes effect).
    _auth_result: tuple[str, str, str, str] | None = None

    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([0.6, 2, 0.6])
    with col:
        with st.container(border=True):
            st.header("Login")

            with st.form("form_login_page"):
                email = st.text_input("Email", key="login_page_email")
                password = st.text_input(
                    "Password", type="password", key="login_page_pass"
                )
                submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                if not email or not password:
                    st.error("Please enter your email and password.")
                else:
                    try:
                        result = login(email.strip(), password)
                        token = result["access_token"]
                        # Fetch profile so we can display the user's real name
                        try:
                            profile = get_me(token)
                            first_name = profile.get("first_name") or ""
                            last_name = profile.get("last_name") or ""
                        except BackendError:
                            first_name = ""
                            last_name = ""
                        _auth_result = (token, email.strip(), first_name, last_name)
                        st.query_params["view"] = "home"
                    except BackendError as exc:
                        st.error(str(exc))

            st.markdown(
                "No account? [Register](?view=register)", unsafe_allow_html=True
            )

    # Inject auth cookies outside any container — prevents rendering artifacts.
    if _auth_result:
        save_auth(*_auth_result)
        st.rerun()

    st.markdown("---")
    _, col_back, _ = st.columns([1, 2, 1])
    with col_back:
        if st.button("← Back to Main Page", key="login_back_home", use_container_width=True):
            st.query_params["view"] = "home"
            st.rerun()
