import streamlit as st
from solution_navigation import show_solution_navigation
from tool_preparation import pre_vs, pre_patent_cpc_mapping, pre_cpc_tree, cpc_interp
import os
from datetime import datetime


# 基于需求查询相关CPC和专利
def query_requirement(_query, _top_k, _cpc_vs, _title_vs, _abstract_vs):
    _cpc_results = _cpc_vs.similarity_search_with_score(_query, _top_k[0])
    _title_results = _title_vs.similarity_search_with_score(_query, _top_k[1])
    _abstract_results = _abstract_vs.similarity_search_with_score(_query, _top_k[2])
    _cpc_results = [_c[0].metadata['source'] for _c in _cpc_results]
    _title_results = [_p[0].metadata['source'] for _p in _title_results]
    _abstract_results = [_p[0].metadata['source'] for _p in _abstract_results]
    return _cpc_results, _title_results, _abstract_results


# 筛选核心CPC
def get_core_cpc(_similar_cpc, _similar_title, _similar_abstract, _patent_cpc):
    _core_cpc_dict = {_cpc: 0 for _cpc in _similar_cpc}
    for _patent in st.session_state["similar_patent"]:
        _cpc = _patent_cpc[_patent]
        for _c in _cpc:
            if _c in _core_cpc_dict:
                _core_cpc_dict[_c] += 1
    _core_cpc_dict = {k: v for k, v in _core_cpc_dict.items() if v > 0}
    _core_cpc_list = sorted(_core_cpc_dict.items(), key=lambda x: x[1], reverse=True)
    return _core_cpc_list


def get_all_technology_selection():
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Searching for core technologies...\n".encode())
    if not st.session_state['tool_preparation']['cpc_vs'] or not st.session_state['tool_preparation']['title_vs'] or not \
            st.session_state['tool_preparation']['abstract_vs']:
        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Preparing the vector store...\n".encode())
        pre_vs()
    if not st.session_state["tool_preparation"]["patent_cpc_map"]:
        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Preparing the patent-cpc mapping...\n".encode())
        pre_patent_cpc_mapping()
    if not st.session_state["tool_preparation"]['cpc_tree']:
        pre_cpc_tree()

    # 确定核心技术需要的数据
    _requirement = st.session_state["conceptual_solution_info"]["requirement"]
    _cpc_vs = st.session_state["tool_preparation"]["cpc_vs"]
    _title_vs = st.session_state["tool_preparation"]["title_vs"]
    _abstract_vs = st.session_state["tool_preparation"]["abstract_vs"]
    _patent_cpc = st.session_state["tool_preparation"]["patent_cpc_map"]

    top_k = (
        st.session_state['relevant_cpc_number'],
        st.session_state['relevant_title_patent_number'],
        st.session_state['relevant_abstract_patent_number']
    )

    # 确定核心CPC
    _cpc_similarity, _title_similarity, _abstract_similarity = query_requirement(_requirement, _top_k=top_k,
                                                                                 _cpc_vs=_cpc_vs, _title_vs=_title_vs,
                                                                                 _abstract_vs=_abstract_vs)
    st.session_state["similar_patent"] = list(set(_title_similarity) | set(_abstract_similarity))
    core_cpc = get_core_cpc(_cpc_similarity, _title_similarity, _abstract_similarity, _patent_cpc)[:st.session_state['core_technology_number']]
    core_cpc = [c[0] for c in core_cpc]

    # 解释核心CPC
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Interpreting the core technologies...\n".encode())

    try_num = 0
    while try_num < st.session_state['maximum_request_number']:
        try:
            return cpc_interp(core_cpc)
        except:
            try_num += 1
            os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Error occurred in interpreting core technologies. Retrying...\n".encode())
            continue

    st.header("Error occurred in interpreting core technologies. Please try again later.")
    st.stop()


def select_all_core_technology():
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Selecting all core technologies...\n".encode())
    for _tech in st.session_state["core_technology_all"]:
        st.session_state["core_technology_select"][_tech] = True
        _core_cpc_feature = st.session_state["core_technology_all"][_tech]["Core Feature"]
        st.session_state["conceptual_solution_info"]["core_technology"][_tech] = _core_cpc_feature


def select_none_core_technology():
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Cleaning all core technologies...\n".encode())
    st.session_state["core_technology_select"] = {tech: False for tech in st.session_state["core_technology_all"].keys()}
    st.session_state["conceptual_solution_info"]["core_technology"] = {}


def select_core_technology():
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Selecting some core technologies...\n".encode())
    for _tech in st.session_state["core_technology_select"]:
        if st.session_state["core_technology_select"][_tech]:
            _core_cpc_feature = st.session_state["core_technology_all"][_tech]["Core Feature"]
            st.session_state["conceptual_solution_info"]["core_technology"][_tech] = _core_cpc_feature
        else:
            st.session_state["conceptual_solution_info"]["core_technology"].pop(_tech, None)


def select_core_technology_module(_core_technology_dict):
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Selecting core technologies...\n".encode())
    st.session_state["core_technology_select"] = {tech: False for tech in _core_technology_dict.keys()}

    _col1, _col2, _ = st.columns([1, 1, 4])
    with _col1:
        select_all = st.button("Select All", use_container_width=True)
    with _col2:
        select_someones = st.button("Select", use_container_width=True)

    # 构建多选模块
    for tech in _core_technology_dict:
        labels = f"***{tech}***: {_core_technology_dict[tech]['Core Feature']}"
        help_text = f"***Technology Feature***: {_core_technology_dict[tech]['Technology Feature']}  \n"
        help_text += f"***Functions***: {', '.join(_core_technology_dict[tech]['Functions'])}".replace('.', '')
        st.session_state["core_technology_select"][tech] = st.checkbox(
            labels,
            value=False,
            help=help_text
        )

    if select_all:
        select_all_core_technology()
        os.write(1, f"{'-' * 80} \n".encode())
        st.rerun()
    if select_someones:
        select_core_technology()
        os.write(1, f"{'-' * 80} \n".encode())
        st.rerun()


def clean_all_follow_info():
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Cleaning all follow information...\n".encode())
    st.session_state["conceptual_solution_info"]["technology_opportunity"] = None
    st.session_state["conceptual_solution_info"]["conceptual_solution"] = None

    st.session_state["technology_opportunity_all"] = []
    st.session_state["conceptual_solution_all"] = []
    st.session_state["conceptual_solution_adjustment"] = False

    st.session_state["technology_opportunity_select"] = 0
    st.session_state["conceptual_solution_select"] = 0


def change_core_technology_module(_core_technology_dict):
    st.write("If you want to change the core technology, please select again.")

    _col1, _col2, _col3, _ = st.columns([1, 1, 1, 3])
    with _col1:
        if st.button("Select All", use_container_width=True):
            select_all_core_technology()
            clean_all_follow_info()
            os.write(1, f"{'-' * 80} \n".encode())
            st.rerun()
    with _col2:
        if st.button("Clean All", use_container_width=True):
            select_none_core_technology()
            clean_all_follow_info()
            os.write(1, f"{'-' * 80} \n".encode())
            st.rerun()
    with _col3:
        select_someones = st.button("Select", use_container_width=True)

    for tech in _core_technology_dict:
        labels = f"***{tech}***: {_core_technology_dict[tech]['Core Feature']}"
        help_text = f"***Technology Feature***: {_core_technology_dict[tech]['Technology Feature']}  \n"
        help_text += f"***Functions***: {', '.join(_core_technology_dict[tech]['Functions'])}".replace('.', '')
        st.session_state["core_technology_select"][tech] = st.checkbox(
            labels,
            value=st.session_state["core_technology_select"][tech],
            help=help_text
        )

    if select_someones:
        select_core_technology()
        clean_all_follow_info()
        os.write(1, f"{'-' * 80} \n".encode())
        st.rerun()


def core_technology_determine():
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Showing Core Technology Page.\n".encode())
    if not st.session_state['api_key']:
        st.header("Please input your API Key first.")
    elif not st.session_state["conceptual_solution_info"]["requirement"]:
        st.header("Please input requirement first.")
    elif not st.session_state["core_technology_all"]:
        with st.spinner("Searching for core technologies···"):
            st.session_state["core_technology_all"] = get_all_technology_selection()
            os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Core Technology Preparation Complete.\n".encode())
            os.write(1, f"{'-' * 80} \n".encode())
            st.rerun()
    elif not st.session_state["conceptual_solution_info"]["core_technology"]:
        st.title("Select Core Technology")
        st.write("Please select core technology here:")
        st.divider()
        select_core_technology_module(st.session_state["core_technology_all"])
    else:
        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Core Technology showed.\n".encode())
        st.title("Core Technology")
        core_technology_text = ""
        for tech, feature in st.session_state["conceptual_solution_info"]["core_technology"].items():
            core_technology_text += f"- ***{tech}***: {feature}  \n"
        st.markdown(core_technology_text)
        st.markdown("Click `Innovation Opportunity` for further design.")
        st.divider()
        change_core_technology_module(st.session_state["core_technology_all"])


def core_technology_page():
    _col1, _, _col2 = st.columns([6.3, 0.2, 3.5])
    with _col2:
        show_solution_navigation()
    with _col1:
        core_technology_determine()
