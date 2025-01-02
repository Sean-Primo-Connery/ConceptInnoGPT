import streamlit as st
import os
from datetime import datetime
from tool_preparation import (re_generate_fm, re_generate_cs)
import time


def download_solution():
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Downloading solution...\n".encode())
    _cs = st.session_state["conceptual_solution_info"]["solution_adjustment"]
    _cs_title = _cs['Title']
    _cs_desc = _cs['Description']
    _cs_func = _cs['Functional Modules']
    _cs_cpc_interp = {}

    _all_cpc_list = []
    for _func in _cs_func:
        _all_cpc_list.extend(_func['applied_technologies'])
    _all_cpc_list = list(set(_all_cpc_list))
    for _cpc in _all_cpc_list:
        _cs_cpc_interp[_cpc] = {
            "Core Feature": st.session_state['tool_preparation']['cs_cpc_interp'][_cpc]['Core Feature'],
            "Technology Feature": st.session_state['tool_preparation']['cs_cpc_interp'][_cpc]['Technology Feature'],
            "Functions": st.session_state['tool_preparation']['cs_cpc_interp'][_cpc]['Functions'],
            "classification": st.session_state['tool_preparation']["cpc_tree"][_cpc]['classification']
        }

    _cs_text = f"## {_cs_title}  \n"
    _cs_text += f"### Description  \n"
    _cs_text += f"{_cs_desc}  \n"
    _cs_text += f"### Functional Modules  \n"
    for _func in _cs_func:
        _cs_text += f"#### {_func['module_name']}  \n"
        _cs_text += f"***Description:*** {_func['description']}  \n"
        _cs_text += f"***Applied Technologies:***  \n"
        for _cpc in _func['applied_technologies']:
            _cs_text += f"--> {_cpc}: {_cs_cpc_interp[_cpc]['Core Feature']}  \n"
    _cs_text += f"  \n  \n  \n"

    _cs_text += f"### More Details  \n"
    for _cpc in _cs_cpc_interp:
        _cs_text += f"#### {_cpc}: {_cs_cpc_interp[_cpc]['Core Feature']}  \n"
        _cs_text += f"***Technology Feature:*** {_cs_cpc_interp[_cpc]['Technology Feature']}  \n"
        _cs_text += f"***Functions:***  \n"
        for _func in _cs_cpc_interp[_cpc]['Functions']:
            _cs_text += f" - {_func}  \n"
        _cs_text += f"  \n"
        _cs_text += f"***Original Definition:*** {_cs_cpc_interp[_cpc]['classification']}  \n"

    file_name = "Adjusted_Conceptual_Solution.md"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(_cs_text)

    return _cs_text, file_name


def adjust_cs_title_description():
    _cs = st.session_state["conceptual_solution_info"]["conceptual_solution"]
    if not st.session_state['adjust_cs_title']:
        _cs_title = _cs['Title']
    else:
        _cs_title = st.session_state['adjust_cs_title']
    if not st.session_state['adjust_cs_desc']:
        _cs_desc = _cs['Description']
    else:
        _cs_desc = st.session_state['adjust_cs_desc']

    st.header(_cs_title)
    st.subheader("Description")
    st.write(_cs_desc)

    # 修正标题与描述
    _col11, _col12 = st.columns([1, 1])
    with _col11:
        with st.popover("Revise Title", use_container_width=True):
            new_title = st.text_input("Title")
            if st.button("Update Title") and new_title:
                os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Updating title to {new_title}...\n".encode())
                st.session_state['adjust_cs_title'] = new_title
                st.rerun()
    with _col12:
        with st.popover("Revise Description", use_container_width=True):
            new_desc = st.text_area("Description")
            if st.button("Update Description") and new_desc:
                os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Updating description to {new_desc}...\n".encode())
                st.session_state['adjust_cs_desc'] = new_desc
                st.rerun()

    # 四个按钮
    _col21, _col22, _col23, _col24 = st.columns([1, 1, 1, 1], vertical_alignment="center")
    with _col21:
        if st.button("Reset Title", use_container_width=True):
            os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Resetting title...\n".encode())
            st.session_state['adjust_cs_title'] = None
            st.rerun()
    with _col22:
        if st.button("Reset Description", use_container_width=True):
            os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Resetting description...\n".encode())
            st.session_state['adjust_cs_desc'] = None
            st.rerun()
    with _col23:
        if st.button("Regenerate", use_container_width=True,
                     help="Regenerate titles and descriptions utilizing LLM and redesigned functional modules. ***Ensure the functional module design is completed to enable activation.***",):
            if all(st.session_state['adjust_cs_func_module_status']) and st.session_state['adjust_cs_func_module']:
                os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Regenerating title and description...\n".encode())
                st.toast("Regenerate the title and description···")
                new_title_desc = re_generate_cs(st.session_state['adjust_cs_func_module'])
                st.session_state['adjust_cs_title'] = new_title_desc['Title']
                st.session_state['adjust_cs_desc'] = new_title_desc['Description']
                st.toast("Regenerate complete!", icon='🎉')
                os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Regenerate complete.\n".encode())
                time.sleep(0.5)
                st.rerun()
            else:
                st.toast("Please complete the functional module design first.")
    with _col24:
        if st.button("Save", use_container_width=True,
                     help="Before saving, please ensure consistency between the conceptual scheme description and the functional modules. ***Ensure the functional module design is completed to enable activation.***"):
            if all(st.session_state['adjust_cs_func_module_status']) and st.session_state['adjust_cs_func_module']:
                os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Saving title and description...\n".encode())
                st.session_state["conceptual_solution_info"]["solution_adjustment"] = {
                    "Title": _cs_title,
                    "Description": _cs_desc,
                    "Functional Modules": st.session_state['adjust_cs_func_module']
                }
                st.rerun()
            else:
                st.toast("Please complete the functional module design first.")


def adjust_cs_functional_modules():
    _org_func_col, _new_func_col = st.columns([3.5, 6.5], gap="small")

    # 辅助新模块生成的CPC解释
    _cs_func = st.session_state["conceptual_solution_info"]["conceptual_solution"]['Functional Modules']
    _all_cpc_list = []
    for _func in _cs_func:
        _all_cpc_list.extend(_func['applied_technologies'])
    _all_cpc_list = list(set(_all_cpc_list))
    for _cpc in _all_cpc_list:
        st.session_state['adjust_cs_cpc_interp'][_cpc] = {
            "Core Feature": st.session_state['tool_preparation']['cs_cpc_interp'][_cpc]['Core Feature'],
            "Technology Feature": st.session_state['tool_preparation']['cs_cpc_interp'][_cpc]['Technology Feature'],
            "Functions": st.session_state['tool_preparation']['cs_cpc_interp'][_cpc]['Functions'],
            "Original definition": st.session_state['tool_preparation']["cpc_tree"][_cpc]['classification']
        }

    _new_func = st.session_state['adjust_cs_func_module']
    _new_func_status = st.session_state['adjust_cs_func_module_status']

    # 显示原始功能模块
    with _org_func_col:
        st.subheader("Original Functional Modules")

        if st.button("Add All to New Modules", use_container_width=True):
            os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Adding all modules to new modules...\n".encode())
            st.session_state['adjust_cs_func_module'] = _cs_func
            st.session_state['adjust_cs_func_module_status'] = [True] * len(_cs_func)
            st.rerun()

        for _func in _cs_func:
            with st.container(border=True):
                _func_text = f"#### {_func['module_name']}  \n"
                _func_text += f"***Description:*** {_func['description']}  \n"
                _func_text += f"***Applied Technologies:***  \n"
                for _cpc in _func['applied_technologies']:
                    _func_text += f"--> {_cpc}: {st.session_state['tool_preparation']['cs_cpc_interp'][_cpc]['Core Feature']}  \n"
                st.markdown(_func_text)

                _in_new_module = False
                if _func in _new_func:
                    _in_new_module = True
                _func_index = _cs_func.index(_func)

                if st.button("Add to New Modules", key=f"{_func_index}_add_to_new", disabled=_in_new_module, use_container_width=True):
                    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Adding module {_func['module_name']} to new modules...\n".encode())
                    st.session_state['adjust_cs_func_module'].append(_func)
                    st.session_state['adjust_cs_func_module_status'].append(True)
                    st.rerun()

    with _new_func_col:
        st.subheader("New Functional Modules")

        # 显示辅助CPC解释
        with st.container(border=True):
            for _cpc in st.session_state['adjust_cs_cpc_interp']:
                markdown_text = f"##### {_cpc}: {st.session_state['adjust_cs_cpc_interp'][_cpc]['Core Feature']}"
                help_text = f"***Technology Feature:*** {st.session_state['adjust_cs_cpc_interp'][_cpc]['Technology Feature']}  \n"
                help_text += f"***Definition:*** {st.session_state['adjust_cs_cpc_interp'][_cpc]['Original definition']}  \n"
                help_text += f"***Functions:***  \n"
                for _func in st.session_state['adjust_cs_cpc_interp'][_cpc]['Functions']:
                    help_text += f"--> {_func.replace('.', '')}  \n"
                st.markdown(markdown_text, help=help_text)

        # 显示新功能模块
        for _new_func_index in range(len(_new_func)):
            with st.container(border=True):
                _new_func_col1, _new_func_col2 = st.columns([8, 2])
                _func = _new_func[_new_func_index]
                # 显示相关内容
                with _new_func_col1:
                    _func_name = st.text_input("Module Name", _func['module_name'], key=f"{_new_func_index}_name")
                    _func_desc = st.text_area("Description", _func['description'], key=f"{_new_func_index}_desc")

                _func_tech = st.segmented_control("Applied Technologies", _all_cpc_list,
                                                  default=_func['applied_technologies'], key=f"{_new_func_index}_tech",
                                                  selection_mode="multi")

                # 处理按钮
                with _new_func_col2:
                    if st.button("Save", key=f"{_new_func_index}_save", disabled=(not _func_name) or (not _func_desc), use_container_width=True):
                        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Saving new module...\n".encode())
                        _new_func[_new_func_index] = {
                            "module_name": _func_name,
                            "description": _func_desc,
                            "applied_technologies": _func_tech,
                        }
                        _new_func_status[_new_func_index] = True
                        st.toast("Save complete!", icon='🎉')
                        time.sleep(0.3)
                        st.rerun()
                    if st.button("Regenerate", key=f"{_new_func_index}_reset", disabled=not _func_tech,
                                 use_container_width=True, help="Regenerate the functional module description based on the selected CPC codes."):
                        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Regenerating module {_func_name}...\n".encode())
                        st.toast("Regenerate the functional module description···")
                        re_generate_fm_info = re_generate_fm(_func_tech)
                        _new_func[_new_func_index] = {
                            "module_name": re_generate_fm_info['module_name'],
                            "description": re_generate_fm_info['description'],
                            "applied_technologies": _func_tech,
                        }
                        _new_func_status[_new_func_index] = True
                        st.toast("Regenerate complete!", icon='🎉')
                        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Regenerate complete.\n".encode())
                        time.sleep(0.3)
                        st.rerun()
                    if st.button("Remove", key=f"{_new_func_index}_remove", use_container_width=True):
                        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Removing module {_func_name}...\n".encode())
                        _new_func.remove(_func)
                        _new_func_status.pop(_new_func_index)
                        st.toast("Remove complete!")
                        time.sleep(0.3)
                        st.rerun()

                    with st.container():
                        _current_func = {
                            "module_name": _func_name,
                            "description": _func_desc,
                            "applied_technologies": _func_tech,
                        }
                        if _current_func == _func and _new_func_status[_new_func_index]:
                            st.success("Saved!")
                        else:
                            _new_func_status[_new_func_index] = False
                            st.warning("Not Saved!")

        # 新功能模块处理按钮
        _new_button_col1, _new_button_col2 = st.columns([1, 1])
        with _new_button_col1:
            if st.button("Add Module", use_container_width=True):
                os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Adding new module...\n".encode())
                st.session_state['adjust_cs_func_module'].append({
                    "module_name": "",
                    "description": "",
                    "applied_technologies": [],
                })
                st.session_state['adjust_cs_func_module_status'].append(False)
                st.rerun()
        with _new_button_col2:
            if st.button("Clean Modules", use_container_width=True):
                os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Cleaning all modules...\n".encode())
                st.session_state['adjust_cs_func_module'] = []
                st.session_state['adjust_cs_func_module_status'] = []
                os.write(1, f"{'-' * 80} \n".encode())
                st.rerun()


def solution_adjustment_page():
    if not st.session_state['api_key']:
        st.header("Please input your API Key first.")
    elif not st.session_state["conceptual_solution_info"]["requirement"]:
        st.header("Please input requirement first.")
    elif not st.session_state["conceptual_solution_info"]["core_technology"]:
        st.header("Please select core technology first.")
    elif not st.session_state["conceptual_solution_info"]["technology_opportunity"]:
        st.header("Please select technology opportunity first.")
    elif not st.session_state["conceptual_solution_info"]["conceptual_solution"]:
        st.header("Please select conceptual solution first.")
    elif not st.session_state["conceptual_solution_adjustment"]:
        st.header(
            "If you need to modify the generated conceptual solution, click on `Adjust` under the `Conceptual Solution` tab.")
    elif not st.session_state["conceptual_solution_info"]["solution_adjustment"]:
        adjust_cs_title_description()
        st.divider()
        adjust_cs_functional_modules()
    else:
        _data, _file_name = download_solution()
        st.markdown(_data)
        _col1, _col2, _ = st.columns([1, 1, 3])
        with _col1:
            st.download_button("Download", data=_data, file_name=f"{_file_name.split('.')[0]}-{datetime.now().strftime('%Y%m%d%H%M%S')}.md", help="Download the adjusted conceptual solution.", use_container_width=True)
        with _col2:
            if st.button("Re-Adjust", use_container_width=True):
                st.session_state["conceptual_solution_info"]["solution_adjustment"] = None
                os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Re-adjusting the solution...\n".encode())
                os.write(1, f"{'-' * 80} \n".encode())
                st.rerun()
