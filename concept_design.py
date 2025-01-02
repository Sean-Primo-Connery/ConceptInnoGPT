import streamlit as st
from solution_navigation import show_solution_navigation
import os
from datetime import datetime
from tool_preparation import patent_retrieval, cs_generate, cpc_interp
import multiprocessing
import json


def get_all_conceptual_solution():
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Searching for conceptual solutions...\n".encode())
    _technology_opportunity = st.session_state["conceptual_solution_info"]["technology_opportunity"]

    # 检索CPC组合
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Retrieving CPC combination...\n".encode())
    _overlap_cpc_list = []
    _similar_patent = st.session_state["similar_patent"]
    overlap_cpc = patent_retrieval(_technology_opportunity, _similar_patent)

    patent_cpc = st.session_state["tool_preparation"]["patent_cpc_map"]
    for _over in overlap_cpc[:st.session_state['conceptual_solution_number']]:
        _src_cpc = patent_cpc[_over[0]]
        _dst_cpc = patent_cpc[_over[1]]
        _over = tuple(set(_src_cpc) & set(_dst_cpc))
        _overlap_cpc_list.append(_over)

    # 生成概念方案
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Generating conceptual solutions...\n".encode())
    _oppo_pair = st.session_state["conceptual_solution_info"]["technology_opportunity"]
    _requirement = st.session_state["conceptual_solution_info"]["requirement"]
    _pcs = st.session_state["technology_opportunity_all"][_oppo_pair]

    _all_cpc_list = []
    _all_cpc_list.extend(_oppo_pair)
    for _cpc_comb in _overlap_cpc_list:
        _all_cpc_list.extend(_cpc_comb)
    _all_cpc_list = list(set(_all_cpc_list))

    _all_cpc_interp_dict = cpc_interp(_all_cpc_list)
    st.session_state["tool_preparation"]['cs_cpc_interp'] = _all_cpc_interp_dict

    model_info = {
        "model_type": st.session_state['model_type'],
        "temperature": st.session_state['temperature'],
        "top_p": st.session_state['top_p'],
        "presence_penalty": st.session_state['presence_penalty'],
        "frequency_penalty": st.session_state['frequency_penalty'],
        "api_key": st.session_state['api_key'],
        "base_url": st.session_state['base_url']
    }
    _model_info_path = f"model_info_{st.session_state['username_logged']}.json"
    with open(_model_info_path, "w") as f:
        json.dump(model_info, f)

    _cs_data_list = []
    for _cpc_comb in _overlap_cpc_list:
        _all_cpc = []
        _all_cpc.extend(_oppo_pair)
        _all_cpc.extend(_cpc_comb)
        _all_cpc_interp = {_cpc: _all_cpc_interp_dict[_cpc] for _cpc in _all_cpc}
        _cs_data_list.append((_oppo_pair, _cpc_comb, _all_cpc_interp, _requirement, _pcs, _model_info_path))

    try_num = 0
    while try_num < st.session_state['maximum_request_number']:
        try:
            with multiprocessing.Pool(processes=8) as pool:
                _cs_list = pool.starmap(cs_generate, _cs_data_list)
            return _cs_list
        except Exception as e:
            try_num += 1
            os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Error occurred in generating conceptual solutions. Retrying...\n".encode())
            continue

    st.header("Error occurred in generating conceptual solutions. Please try again later.")
    st.stop()


def make_cs_caption(cs_list):
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Making conceptual solution captions...\n".encode())
    _cs_label_list = []
    _cs_caption_list = []
    for _cs in cs_list:
        radio_text = ""
        caption_text = ""

        radio_text += f"***{_cs['Title']}***  \n"
        radio_text += f"{_cs['Description']}  \n"

        caption_text += f"**Functional Modules:**  \n"
        for _func in _cs['Functional Modules']:
            module_name = _func['module_name']
            module_desc = _func['description']
            module_technology = _func['applied_technologies']

            caption_text += f"--> ***{module_name}***  \n"
            for _tech in module_technology:
                caption_text += f"----> **{_tech}**: {st.session_state['tool_preparation']['cs_cpc_interp'][_tech]['Core Feature']}  \n"
            caption_text += f"**Description:** {module_desc}  \n  \n"

        _cs_label_list.append(radio_text)
        _cs_caption_list.append(caption_text)

    return _cs_label_list, _cs_caption_list


def select_conceptual_solution(cs_list):
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Selecting conceptual solution...\n".encode())
    _cs_label_list, _cs_caption_list = make_cs_caption(cs_list)

    select_to = st.button("Select", key="select_conceptual_solution")
    _selected_oppo = st.radio("Please select conceptual solution here:", _cs_label_list, captions=_cs_caption_list,
                              index=st.session_state["conceptual_solution_select"])

    if select_to:
        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Conceptual solution selected.\n".encode())
        select_index = _cs_label_list.index(_selected_oppo)
        st.session_state["conceptual_solution_select"] = select_index
        st.session_state["conceptual_solution_info"]["conceptual_solution"] = cs_list[select_index]
        os.write(1, f'{"-" * 80} \n'.encode())
        st.rerun()


def change_conceptual_solution(cs_list):
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Changing conceptual solution...\n".encode())
    _cs_label_list, _cs_caption_list = make_cs_caption(cs_list)

    _col1, _col2 = st.columns([1, 4])
    with _col1:
        select_to = st.button("Change", key="change_conceptual_solution", use_container_width=True)
    _selected_oppo = st.radio("If you want to change the conceptual solution, please select again.", _cs_label_list, captions=_cs_caption_list,
                              index=st.session_state["conceptual_solution_select"])

    if select_to:
        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Conceptual solution changed.\n".encode())
        select_index = _cs_label_list.index(_selected_oppo)
        st.session_state["conceptual_solution_select"] = select_index
        st.session_state["conceptual_solution_info"]["conceptual_solution"] = cs_list[select_index]

        st.session_state["conceptual_solution_adjustment"] = False

        os.write(1, f'{"-" * 80} \n'.encode())
        st.rerun()


def download_conceptual_solution():
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Downloading conceptual solution...\n".encode())
    _cs = st.session_state["conceptual_solution_info"]["conceptual_solution"]
    _cs_title = _cs['Title']
    _cs_desc = _cs['Description']
    _cs_func = _cs['Functional Modules']

    _cs_text = f"## {_cs_title}  \n"
    _cs_text += f"### Description  \n"
    _cs_text += f"{_cs_desc}  \n"
    _cs_text += f"### Functional Modules  \n"
    for _func in _cs_func:
        _cs_text += f"#### {_func['module_name']}  \n"
        _cs_text += f"**Description:** {_func['description']}  \n"
        _cs_text += f"**Applied Technologies:**  \n"
        for _cpc in _func['applied_technologies']:
            _cs_text += f"--> {_cpc}: {st.session_state['tool_preparation']['cs_cpc_interp'][_cpc]['Core Feature']}  \n"
    _cs_text += f"  \n"

    _all_cpc_list = []
    for _func in _cs_func:
        _all_cpc_list.extend(_func['applied_technologies'])
    _all_cpc_list = list(set(_all_cpc_list))

    _cs_text += f"### More Details  \n"
    for _cpc in _all_cpc_list:
        _cs_text += f"#### {_cpc}: {st.session_state['tool_preparation']['cs_cpc_interp'][_cpc]['Core Feature']}  \n"
        _cs_text += f"**Technology Feature:** {st.session_state['tool_preparation']['cs_cpc_interp'][_cpc]['Technology Feature']}  \n"
        _cs_text += f"**Functions:**  \n"
        for _func in st.session_state['tool_preparation']['cs_cpc_interp'][_cpc]['Functions']:
            _cs_text += f" - {_func}  \n"
        _cs_text += f"  \n"
        _cs_text += f"**Original Definition:** {st.session_state['tool_preparation']['cpc_tree'][_cpc]['classification']}  \n"

    file_name = "Conceptual_Solution.md"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(_cs_text)

    return _cs_text, file_name


def active_conceptual_solution_adjustment():
    st.session_state['conceptual_solution_adjustment'] = True

    st.session_state["conceptual_solution_info"]["solution_adjustment"] = None

    st.session_state['adjust_cs_title'] = None
    st.session_state['adjust_cs_desc'] = None
    st.session_state['adjust_cs_func_module'] = []
    st.session_state['adjust_cs_cpc_interp'] = {}
    st.session_state['regenerate_check'] = False
    st.session_state['adjust_cs_func_module_status'] = []


def conceptual_solution_design():
    if not st.session_state['api_key']:
        st.header("Please input your API Key first.")
    elif not st.session_state["conceptual_solution_info"]["requirement"]:
        st.header("Please input requirement first.")
    elif not st.session_state["conceptual_solution_info"]["core_technology"]:
        st.header("Please select core technology first.")
    elif not st.session_state["conceptual_solution_info"]["technology_opportunity"]:
        st.header("Please select technology opportunity first.")
    elif not st.session_state["conceptual_solution_all"]:
        with st.spinner("Searching for conceptual solutions···"):
            st.session_state["conceptual_solution_all"] = get_all_conceptual_solution()
            os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Conceptual Solution Preparation Complete.\n".encode())
            os.write(1, f"{'-' * 80} \n".encode())
            st.rerun()
    elif not st.session_state["conceptual_solution_info"]["conceptual_solution"]:
        st.title("Select Conceptual Solution")
        select_conceptual_solution(st.session_state["conceptual_solution_all"])
    else:
        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Conceptual Solution showed.\n".encode())

        st.title("Conceptual Solution")
        concept_design_text = f"### {st.session_state['conceptual_solution_info']['conceptual_solution']['Title']}  \n"
        concept_design_text += f"#### Description  \n"
        concept_design_text += f"{st.session_state['conceptual_solution_info']['conceptual_solution']['Description']}  \n"
        concept_design_text += f"#### Functional Modules  \n"
        for _func in st.session_state['conceptual_solution_info']['conceptual_solution']['Functional Modules']:
            concept_design_text += f"##### {_func['module_name']}  \n"
            concept_design_text += f"**Description:** {_func['description']}  \n"
            concept_design_text += f"**Applied Technologies:**  \n"
            for _cpc in _func['applied_technologies']:
                concept_design_text += f"--> {_cpc}: {st.session_state['tool_preparation']['cs_cpc_interp'][_cpc]['Core Feature']}  \n"
        concept_design_text += f"  \n"
        st.markdown(concept_design_text)

        _data, _file_name = download_conceptual_solution()
        _col1, _col2, _ = st.columns([2, 2, 6])
        with _col1:
            st.download_button("Download", _data, file_name=f"{_file_name.split('.')[0]}-{datetime.now().strftime('%Y%m%d%H%M%S')}.md", key="download_conceptual_solution",
                               use_container_width=True)
        with _col2:
            if st.button("Adjust", key="adjust_conceptual_solution", use_container_width=True):
                active_conceptual_solution_adjustment()
                os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Adjusting conceptual solution...\n".encode())
                os.write(1, f'{"-" * 80} \n'.encode())

        st.write("If you wish to modify the current conceptual solution, please click the `Adjust` button and make changes under `Solution Adjustment`.")

        st.divider()

        change_conceptual_solution(st.session_state["conceptual_solution_all"])


def concept_design_page():
    _col1, _, _col2 = st.columns([6.3, 0.2, 3.5])
    with _col2:
        show_solution_navigation()
    with _col1:
        conceptual_solution_design()
