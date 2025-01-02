import streamlit as st
from solution_navigation import show_solution_navigation
from tool_preparation import (pre_all_cpc_list,
                              pre_cpc_coo_data,
                              compute_feature,
                              pre_prediction_model,
                              opportunity_filter,
                              computer_similarity,
                              pre_cpc_embedding,
                              pre_cpc_tree,
                              to_interp
                              )
import os
from datetime import datetime


def get_all_technology_opportunity():
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Searching for technology opportunities...\n".encode())

    # 准备所有链接
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Preparing all links...\n".encode())
    _core_cpc_list = list(st.session_state["conceptual_solution_info"]["core_technology"].keys())
    if not st.session_state["tool_preparation"]["all_cpc_list"]:
        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Preparing all CPC list...\n".encode())
        pre_all_cpc_list()
    _all_cpc = st.session_state["tool_preparation"]["all_cpc_list"]
    _all_oppo = []
    for src in _core_cpc_list:
        for dst in _all_cpc:
            if src != dst:
                _all_oppo.append((src, dst))

    # 计算链接特征数据
    if not st.session_state["tool_preparation"]["cpc_coo_data"]:
        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Preparing the CPC-COO data...\n".encode())
        pre_cpc_coo_data()
    _to_data = []
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Computing the feature data...\n".encode())
    for _oppo in _all_oppo:
        _feature = compute_feature(_oppo, st.session_state["tool_preparation"]["cpc_coo_data"])
        _to_data.append(_feature)

    # 计算链接可能性
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Predicting the probability...\n".encode())
    if not st.session_state["tool_preparation"]["scaler"] or not st.session_state["tool_preparation"][
        "prediction_model"]:
        pre_prediction_model()
    _to_data = st.session_state["tool_preparation"]["scaler"].transform(_to_data)
    _to_pred = st.session_state["tool_preparation"]["prediction_model"].predict_proba(_to_data)[:, 1]
    _index_list = sorted(range(len(_to_pred)), key=lambda x: _to_pred[x], reverse=True)
    _pred_oppo = [(_all_oppo[i], _to_pred[i]) for i in _index_list]

    # 筛选技术机会
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Filtering technology opportunities...\n".encode())
    if not st.session_state["tool_preparation"]['cpc_embedding']:
        pre_cpc_embedding()
    if not st.session_state["tool_preparation"]['cpc_tree']:
        pre_cpc_tree()
    _filtered_oppo = opportunity_filter(_pred_oppo,
                                        _proba_threshold=st.session_state['technology_opportunity_filtering_threshold'])
    _oppo_score = [(oppo[0], oppo[1], computer_similarity(oppo[:2])) for oppo in _filtered_oppo]
    _oppo_score_sorted = sorted(_oppo_score, key=lambda x: x[2], reverse=True)[
                         :st.session_state['technology_opportunity_number']]

    if not _oppo_score_sorted:
        return {}

    # 解释技术机会
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Interpreting technology opportunities...\n".encode())

    try_num = 0
    while try_num < st.session_state['maximum_request_number']:
        try:
            return to_interp(_oppo_score_sorted)
        except:
            try_num += 1
            os.write(1,
                     f"[{datetime.now().strftime('%H:%M:%S')}] Interpreting technology opportunities failed, try again...\n".encode())
            continue

    st.header("Error occurred in interpreting innovation opportunities,  Please try again later.")
    st.stop()


def make_oppo_caption(_all_oppo):
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Making technology opportunity captions...\n".encode())
    _oppo_select_list = []
    _oppo_captions = []
    _all_oppo_list = list(_all_oppo.keys())
    for _oppo in _all_oppo_list:
        _radio_text = ""
        _caption_text = ""

        _cpc_pair = _oppo[0] + " & " + _oppo[1]
        _radio_text += f"***{_all_oppo[_oppo]['Title']}***  \n"
        _radio_text += f"**Integration:** {_cpc_pair}  \n"
        for _cpc in _oppo:
            _radio_text += f"--> ***{_cpc}***: {st.session_state['tool_preparation']['to_cpc_interp'][_cpc]['Core Feature']}  \n"

        _caption_text += f"**More Details:**  \n"
        _caption_text += f"{_all_oppo[_oppo]['Integration']}  \n"
        _caption_text += f"**Purposes:**  {_all_oppo[_oppo]['Purposes']}  \n"
        _caption_text += f"**Core Functions:**  \n"
        for _func in _all_oppo[_oppo]['Core Functions']:
            _caption_text += f"--> {_func}  \n"

        _oppo_select_list.append(_radio_text)
        _oppo_captions.append(_caption_text)

    return _oppo_select_list, _oppo_captions, _all_oppo_list


def select_technology_opportunity(_all_oppo):
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Selecting innovation opportunity...\n".encode())
    _oppo_select_list, _oppo_captions, _all_oppo_list = make_oppo_caption(_all_oppo)

    select_to = st.button("Select", key="select_technology_opportunity")
    _selected_oppo = st.radio("Please select innovation opportunity here:", _oppo_select_list, captions=_oppo_captions,
                              index=st.session_state["technology_opportunity_select"])

    if select_to:
        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Technology opportunity selected.\n".encode())
        select_index = _oppo_select_list.index(_selected_oppo)
        st.session_state["technology_opportunity_select"] = select_index
        st.session_state["conceptual_solution_info"]["technology_opportunity"] = _all_oppo_list[select_index]
        os.write(1, f'{"-" * 80} \n'.encode())
        st.rerun()


def change_technology_opportunity(_all_oppo):
    _oppo_select_list, _oppo_captions, _all_oppo_list = make_oppo_caption(_all_oppo)

    _col1, _ = st.columns([1, 4])
    with _col1:
        select_to = st.button("Change", key="change_technology_opportunity")
    _selected_oppo = st.radio("If you want to change the innovation opportunity, please select again.",
                              _oppo_select_list, captions=_oppo_captions,
                              index=st.session_state["technology_opportunity_select"])

    if select_to:
        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Technology opportunity changed.\n".encode())
        select_index = _oppo_select_list.index(_selected_oppo)
        st.session_state["technology_opportunity_select"] = select_index
        st.session_state["conceptual_solution_info"]["technology_opportunity"] = _all_oppo_list[select_index]

        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Cleaning all follow information...\n".encode())
        st.session_state["conceptual_solution_info"]["conceptual_solution"] = None
        st.session_state["conceptual_solution_select"] = 0
        st.session_state["conceptual_solution_all"] = []
        st.session_state["conceptual_solution_adjustment"] = False
        os.write(1, f'{"-" * 80} \n'.encode())
        st.rerun()


def technology_opportunity_discovery():
    if not st.session_state['api_key']:
        st.header("Please input your API Key first.")
    elif not st.session_state["conceptual_solution_info"]["requirement"]:
        st.header("Please input requirement first.")
    elif not st.session_state["conceptual_solution_info"]["core_technology"]:
        st.header("Please select core technology first.")
    elif not st.session_state["technology_opportunity_all"]:
        with st.spinner("Searching for technology opportunities···"):
            all_oppo = get_all_technology_opportunity()
        if all_oppo:
            st.session_state["technology_opportunity_all"] = all_oppo
            os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Technology opportunities found.\n".encode())
            os.write(1, f"{'-' * 80} \n".encode())
            st.rerun()
        else:
            st.header("No innovation opportunities found")
            os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] No technology opportunities found.\n".encode())
            os.write(1, f"{'-' * 80} \n".encode())
            st.stop()
    elif not st.session_state["conceptual_solution_info"]["technology_opportunity"]:
        st.title("Select Innovation Opportunity")
        select_technology_opportunity(st.session_state["technology_opportunity_all"])
    else:
        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Technology opportunity showed.\n".encode())
        st.title("Innovation Opportunity")
        technology_opportunity_text = ""
        key_oppo = st.session_state["conceptual_solution_info"]["technology_opportunity"]
        technology_opportunity_text += f"### {st.session_state['technology_opportunity_all'][key_oppo]['Title']}  \n"
        technology_opportunity_text += f"#### Integration: ***{key_oppo[0]} & {key_oppo[1]}***  \n"
        for _cpc in key_oppo:
            technology_opportunity_text += f"- ***{_cpc}***: {st.session_state['tool_preparation']['to_cpc_interp'][_cpc]['Core Feature']}  \n"
        technology_opportunity_text += f"\n"
        technology_opportunity_text += f"{st.session_state['technology_opportunity_all'][key_oppo]['Integration']}  \n"
        technology_opportunity_text += f"#### Purposes  \n"
        technology_opportunity_text += f"{st.session_state['technology_opportunity_all'][key_oppo]['Purposes']}  \n"
        technology_opportunity_text += f"#### Core Functions:  \n"
        for _func in st.session_state['technology_opportunity_all'][key_oppo]['Core Functions']:
            technology_opportunity_text += f"- {_func}  \n"
        technology_opportunity_text += f"\n"

        st.markdown(technology_opportunity_text)

        st.markdown("Click `Conceptual Solution` for further design.")
        st.divider()

        change_technology_opportunity(st.session_state["technology_opportunity_all"])


def technology_opportunity_page():
    _col1, _, _col2 = st.columns([6.3, 0.2, 3.5])
    with _col2:
        show_solution_navigation()
    with _col1:
        technology_opportunity_discovery()
