"""Launcher for the Model Cards Writing Tool."""
import streamlit as st

from app.ui.screens.main import main

if __name__ == "__main__":
    if "runpage" not in st.session_state:
        st.session_state.runpage = main
    st.session_state.runpage()
