import streamlit as st
import os
from datetime import datetime


def show_solution_navigation():
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Showing Solution Navigation.\n".encode())
    with st.container(border=True):
        st.header("Navigation")
        st.caption("Current conceptual solution is as follows:")

        st.subheader("Requirement")
        requirement = st.session_state["conceptual_solution_info"]["requirement"]
        requirement = requirement if requirement else "No requirement input yet."
        st.write(requirement)

        st.subheader("Core Technology")
        if st.session_state["conceptual_solution_info"]["core_technology"]:
            core_technology = ""
            for tech, feature in st.session_state["conceptual_solution_info"]["core_technology"].items():
                core_technology += f"- ***{tech}***: {feature}  \n"
            with st.expander("Click to check all core technologies.", expanded=False):
                st.write(core_technology)
        else:
            st.write("No core technology was selected.")

        st.subheader("Innovation Opportunity")
        technology_opportunity = st.session_state["conceptual_solution_info"]["technology_opportunity"]
        if technology_opportunity:
            title = st.session_state["technology_opportunity_all"][technology_opportunity]["Title"]
            integration = st.session_state["technology_opportunity_all"][technology_opportunity]["Integration"]
            st.markdown(f"###### {title}  \n{integration}  \n")
            purposes = st.session_state["technology_opportunity_all"][technology_opportunity]["Purposes"]
            core_functions = st.session_state["technology_opportunity_all"][technology_opportunity]["Core Functions"]
            with st.expander("Click to access more information.", expanded=False):
                more_details = ""
                more_details += f"**Integration:** {technology_opportunity[0]} & {technology_opportunity[1]}  \n"
                for _cpc in technology_opportunity:
                    more_details += f"- ***{_cpc}***: {st.session_state['tool_preparation']['to_cpc_interp'][_cpc]['Core Feature']}  \n"
                more_details += f"\n"
                more_details += f"**Purposes:**  {purposes}  \n\n"
                more_details += f"**Core Functions:**  \n"
                for _func in core_functions:
                    more_details += f"- {_func}  \n"
                st.markdown(more_details)
        else:
            st.write("No innovation opportunity was selected.")

