import streamlit as st
import Login
import Sidebar
import MainPage
import os
from datetime import datetime


def init_app():
    st.session_state['username_logged'] = None
    st.session_state["sidebar_init_complete"] = False
    st.session_state['logged_in'] = False
    st.session_state['current_page'] = "main_page"
    st.session_state['api_key'] = None
    st.session_state['base_url'] = "https://api.openai.com/v1"
    st.session_state["app_init_complete"] = True

    st.session_state["conceptual_solution_info"] = {
        "requirement": "",
        "core_technology": {},
        "technology_opportunity": None,
        "conceptual_solution": None,
    }
    st.session_state["similar_patent"] = []
    st.session_state["core_technology_all"] = []
    st.session_state["technology_opportunity_all"] = []
    st.session_state["conceptual_solution_all"] = []

    st.session_state["conceptual_solution_adjustment"] = False

    st.session_state["core_technology_select"] = {}
    st.session_state["technology_opportunity_select"] = 0
    st.session_state["conceptual_solution_select"] = 0

    st.session_state["tool_preparation"] = {
        "cpc_vs": None,
        "title_vs": None,
        "abstract_vs": None,

        "patent_cpc_map": None,
        "cpc_patent_map": None,
        "cpc_tree": None,
        "all_cpc_list": None,
        "cpc_coo_data": None,
        "cpc_embedding": None,

        'to_cpc_interp': None,
        'cs_cpc_interp': None,

        "prediction_model": None,
        "scaler": None,
    }

    st.session_state['tabs_state'] = {
        "Input Requirement": False,
        "Core Technology": False,
        "Technology Opportunity": False,
        "Conceptual Solution": False,
        "Solution Adjustment": False,
    }


def main():
    if "app_init_complete" not in st.session_state or not st.session_state["app_init_complete"]:
        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Initializing the app...\n".encode())
        init_app()

    if st.session_state['logged_in']:
        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Showing main page.\n".encode())
        st.set_page_config(layout="wide")
        Sidebar.create_sidebar()
        if st.session_state.current_page == "main_page":
            MainPage.functions()
    else:
        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Showing login page.\n".encode())
        st.set_page_config(layout="centered")
        Login.show_login_page()


if __name__ == "__main__":
    main()
