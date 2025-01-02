import streamlit as st
from solution_navigation import show_solution_navigation
import os
from datetime import datetime


def requirement_input():
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Showing Requirement Input Page.\n".encode())
    if not st.session_state['api_key']:
        st.header("Please input your API Key first.")
    elif not st.session_state["conceptual_solution_info"]["requirement"]:
        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Requirement inputting...\n".encode())
        st.title("Input Requirement")
        st.write("Please input your requirement here:")
        requirement = st.chat_input("Design Requirement")
        if requirement:
            os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Requirement input: {requirement}.\n".encode())
            st.session_state["conceptual_solution_info"]["requirement"] = requirement
            os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Requirement input complete.\n".encode())
            os.write(1, f"{'-' * 80} \n".encode())
            st.rerun()
    else:
        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Requirement showed.\n".encode())
        st.title("Requirement")
        st.subheader(st.session_state["conceptual_solution_info"]["requirement"])
        st.markdown("""Click `Core Technology` for further design.""")
        st.divider()
        st.write("If you want to change the requirement, please input your new requirement here:")
        requirement = st.chat_input("Design Requirement")
        if requirement:
            os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Requirement changed to {requirement}.\n".encode())

            st.session_state["conceptual_solution_info"]["requirement"] = requirement
            st.session_state["conceptual_solution_info"]["core_technology"] = {}
            st.session_state["conceptual_solution_info"]["technology_opportunity"] = None
            st.session_state["conceptual_solution_info"]["conceptual_solution"] = None

            st.session_state["core_technology_all"] = []
            st.session_state["technology_opportunity_all"] = []
            st.session_state["conceptual_solution_all"] = []

            st.session_state["similar_patent"] = []
            st.session_state["conceptual_solution_adjustment"] = False

            st.session_state["core_technology_select"] = {}
            st.session_state["technology_opportunity_select"] = 0
            st.session_state["conceptual_solution_select"] = 0

            os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Requirement changed complete.\n".encode())
            os.write(1, f"{'-' * 80} \n".encode())

            st.rerun()


def requirement_page():
    _col1, _, _col2 = st.columns([6.3, 0.2, 3.5])
    with _col2:
        show_solution_navigation()
    with _col1:
        requirement_input()
