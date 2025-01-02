import streamlit as st
from requirement_input import requirement_page
from core_technology import core_technology_page
from technology_opportunity import technology_opportunity_page
from concept_design import concept_design_page
from solution_adjustment import solution_adjustment_page


function_tabs = [
    "  Input Requirement  ",
    "  Core Technology  ",
    "  Innovation Opportunity  ",
    "  Conceptual Solution  ",
    "  Solution Adjustment  ",
]


def functions():
    ir, ct, to, cs, sa = st.tabs(function_tabs)

    with ir:
        requirement_page()
    with ct:
        core_technology_page()
    with to:
        technology_opportunity_page()
    with cs:
        concept_design_page()
    with sa:
        solution_adjustment_page()


if __name__ == "__main__":
    functions()
