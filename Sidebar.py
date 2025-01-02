import streamlit as st
import time
from langchain_openai import ChatOpenAI
import os
from datetime import datetime


def init_sidebar():
    if not st.session_state["sidebar_init_complete"]:
        init_default_params()
        st.session_state["sidebar_init_complete"] = True


def init_default_params():
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Initializing default parameters...\n".encode())
    st.session_state['model_type'] = "gpt-4o-mini"
    st.session_state['temperature'] = 0.7
    st.session_state['top_p'] = 1.0
    st.session_state['presence_penalty'] = 0.0
    st.session_state['frequency_penalty'] = 0.0

    st.session_state['core_technology_number'] = 50
    st.session_state['technology_opportunity_number'] = 20
    st.session_state['conceptual_solution_number'] = 5

    st.session_state['relevant_cpc_number'] = 200
    st.session_state['relevant_title_patent_number'] = 300
    st.session_state['relevant_abstract_patent_number'] = 300

    st.session_state['technology_opportunity_filtering_threshold'] = 0.99

    st.session_state['maximum_request_number'] = 3


def add_logo():
    st.title("ConceptInnoGPT")
    st.caption("Looking for innovative conceptual solutions?  \n Here you go!!!")


def show_help():
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Looking for help...\n".encode())
    with st.container():
        _, _col = st.columns([8, 1])
        with _col:
            if st.button("Close", use_container_width=True):
                st.session_state['current_page'] = "main_page"
                os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Close help page.\n".encode())
                os.write(1, f"{'-'*80} \n".encode())
                st.rerun()
        st.markdown("""
            ## Guidance
            ### Essential settings
            - Click the `Set` button
            - Input your API Key and Base URL
            - Click the `Test and Save` button to validate your API Key
            - Click the `Close` button to close the setting page
            
            ### Configurable settings
            ##### 1. Process parameters
            - Click the `Set` button
            - Adjust the sliders:
                - `Core Technology Quantity`: The number of recommended Core Technology items.
                - `Innovation Opportunity Quantity`: The number of recommended Innovation Opportunity items.
                - `Conceptual Solution Quantity`: The number of recommended Conceptual Solution items.
                - `Relevant CPC Quantity`: The number of retrieved relevant CPC items.
                - `Relevant Patent Quantity Based on Patent Titles`: The number of relevant patent items retrieved based on patent titles.
                - `Relevant Patent Quantity Based on Patent Abstracts`: The number of relevant patent items retrieved based on patent abstracts.
                - `Innovation Opportunity Filtering Threshold`: The threshold of filtering Innovation Opportunity items.
                - `Maximum Request Number`: The maximum number of requests for each query.
            - Click the `Set` button to save the settings
            - Click the `Close` button to close the setting page
            ##### 2. Model parameters
            - `Model Type`: The model type determines the model's size and capabilities.
            - `Temperature`: The temperature setting controls the randomness of the output.
            - `Top P`: 'Top-p' sampling focuses on the model's top predictions.
            - `Presence Penalty`: Positive values penalize new tokens based on whether they already appear in the generated text.
            - `Frequency Penalty`: Positive values penalize new tokens based on their existing frequency in the generated text.
            
            ### Workflow
            - Click the `Input Requirement` tab to input your requirement
            - Click the `Core Technology` tab to select core technology
            - Click the `Innovation Opportunity` tab to select innovation opportunity
            - Click the `Conceptual Solution` tab to select conceptual solution
            - Click the "Adjust" button if you want to adjust the selected conceptual solution
            - Click the `Solution Adjustment` tab to adjust the selected conceptual solution
            
            ### Notice
            - Please refrain from adjusting parameters during program execution
            - The program's runtime is influenced by the response speed of OpenAI's API
            - Refreshing the page will result in the loss of all data
            - Please ensure that the API Key supports the model you have selected
            - GPT cannot always produce valid JSON format; the previous task can be rerun to ensure GPT outputs valid JSON format in the next task.
            - The system operates in a lazy mode, loading data only when necessary—that is, the first time the data is required. Consequently, the initial execution is relatively slow.
        """)


def check_and_save_api_key(_api_key, _base_url):
    with st.spinner(f"Validating API Key..."):
        try:
            os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Validating API Key...\n".encode())
            _llm = ChatOpenAI(model="gpt-4o-mini", api_key=_api_key, base_url=_base_url)
            _llm.invoke("Hello, World!")
            st.success("API Key is valid!")
            os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] API Key is valid!\n".encode())
            st.session_state['api_key'] = _api_key
            st.session_state['base_url'] = _base_url
            st.session_state["tool_preparation"]["cpc_vs"] = None
            st.session_state["tool_preparation"]["title_vs"] = None
            st.session_state["tool_preparation"]['abstract_vs'] = None
            time.sleep(1)
            st.rerun()
        except Exception as e:
            os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] API Key is invalid!\n{e}\n".encode())
            st.error(f"API Key is invalid!\n {e}")


def clean_api_key():
    st.session_state['api_key'] = None
    st.session_state['base_url'] = "https://api.openai.com/v1"
    st.session_state["tool_preparation"]["cpc_vs"] = None
    st.session_state["tool_preparation"]["title_vs"] = None
    st.session_state["tool_preparation"]['abstract_vs'] = None
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Clean API Key.\n".encode())
    os.write(1, f"{'-'*80} \n".encode())


def set_api_key():
    with st.form("api_form"):
        st.subheader("Set [API_Key] and [Base_URL]")

        cur_api_key, cur_base_url = st.session_state['api_key'], st.session_state['base_url']
        current_api_key = cur_api_key[:8] + "·" * 36 + cur_api_key[-8:] if cur_api_key else "No API Key Provided"

        api_key = st.text_input("Input Your API Key", type="password", value=cur_api_key)  # 隐藏输入内容
        base_url = st.text_input("Input the Base URL of the API Key", value=cur_base_url)

        st.write("- Current API Key: ", current_api_key)
        st.write("- Current Base URL: ", cur_base_url)

        _col1, _col2, _col3, _ = st.columns([3, 2, 2.5, 4])
        with _col1:
            test_and_save = st.form_submit_button("Test and Save", use_container_width=True)
        with _col2:
            close = st.form_submit_button("Close", use_container_width=True)
        with _col3:
            clean = st.form_submit_button("Clean API", use_container_width=True)

        if test_and_save:
            if not api_key:
                st.error("Please input your API Key at Least.")
            else:
                check_and_save_api_key(api_key, base_url)

        if close:
            st.session_state['current_page'] = "main_page"
            os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Close API Key setting page.\n".encode())
            os.write(1, f"{'-'*80} \n".encode())
            st.rerun()

        if clean:
            clean_api_key()
            st.toast("API Key has been cleaned.")
            time.sleep(0.5)
            st.rerun()

    with st.container(border=True):
        st.subheader("Set the recommended or retrieval quantity.")
        st.slider(
            label="Core Technology Quantity",
            min_value=5,
            max_value=100,
            value=st.session_state['core_technology_number'],
            step=1,
            help="The number of recommended Core Technology items.",
            key='core_technology_number_slider',
        )
        st.slider(
            label="Innovation Opportunity Quantity",
            min_value=1,
            max_value=50,
            value=st.session_state['technology_opportunity_number'],
            step=1,
            help="The number of recommended Innovation Opportunity items.",
            key='technology_opportunity_number_slider',
        )
        st.slider(
            label="Conceptual Solution Quantity",
            min_value=1,
            max_value=20,
            value=st.session_state['conceptual_solution_number'],
            step=1,
            help="The number of recommended Conceptual Solution items.",
            key='conceptual_solution_number_slider',
        )
        st.slider(
            label="Relevant CPC Quantity",
            min_value=100,
            max_value=300,
            value=st.session_state['relevant_cpc_number'],
            step=10,
            help="The number of retrieved relevant CPC items.",
            key='relevant_cpc_number_slider',
        )
        st.slider(
            label="Relevant Patent Quantity Based on Patent Titles",
            min_value=50,
            max_value=1000,
            value=st.session_state['relevant_title_patent_number'],
            step=10,
            help="The number of relevant patent items retrieved based on patent titles.",
            key='relevant_title_patent_number_slider',
        )
        st.slider(
            label="Relevant Patent Quantity Based on Patent Abstracts",
            min_value=50,
            max_value=1000,
            value=st.session_state['relevant_abstract_patent_number'],
            step=10,
            help="The number of relevant patent items retrieved based on patent abstracts.",
            key='relevant_abstract_patent_number_slider',
        )
        st.slider(
            label="Innovation Opportunity Filtering Threshold",
            min_value=0.9,
            max_value=1.0,
            value=st.session_state['technology_opportunity_filtering_threshold'],
            step=0.01,
            help="The threshold of filtering Innovation Opportunity items.",
            key='technology_opportunity_filtering_threshold_slider',
        )
        st.slider(
            label="Maximum Request Number",
            min_value=1,
            max_value=10,
            value=st.session_state['maximum_request_number'],
            step=1,
            help="The maximum number of requests for each query.",
            key='maximum_request_number_slider',
        )
        _col1, _col2, _col3, _ = st.columns([1, 1, 1, 3])
        with _col1:
            if st.button("Set", use_container_width=True, key="set_recommended_number"):
                st.session_state['core_technology_number'] = st.session_state.core_technology_number_slider
                st.session_state[
                    'technology_opportunity_number'] = st.session_state.technology_opportunity_number_slider
                st.session_state['conceptual_solution_number'] = st.session_state.conceptual_solution_number_slider
                st.session_state['relevant_cpc_number'] = st.session_state.relevant_cpc_number_slider
                st.session_state['relevant_title_patent_number'] = st.session_state.relevant_title_patent_number_slider
                st.session_state[
                    'relevant_abstract_patent_number'] = st.session_state.relevant_abstract_patent_number_slider
                st.session_state['technology_opportunity_filtering_threshold'] = st.session_state['technology_opportunity_filtering_threshold_slider']
                st.session_state['maximum_request_number'] = st.session_state['maximum_request_number_slider']
                os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Set recommended number complete.\n".encode())
                st.toast("Parameters have been set.")
                time.sleep(0.5)
                st.rerun()
        with _col2:
            if st.button("Close", use_container_width=True, key="close_recommended_number"):
                st.session_state['current_page'] = "main_page"
                os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Close recommended number setting page.\n".encode())
                os.write(1, f"{'-'*80} \n".encode())
                st.rerun()
        with _col3:
            if st.button("Reset", use_container_width=True, key="reset_recommended_number"):
                st.session_state['core_technology_number'] = 50
                st.session_state['technology_opportunity_number'] = 20
                st.session_state['conceptual_solution_number'] = 5
                st.session_state['relevant_cpc_number'] = 200
                st.session_state['relevant_title_patent_number'] = 300
                st.session_state['relevant_abstract_patent_number'] = 300
                st.session_state['technology_opportunity_filtering_threshold'] = 0.99
                st.session_state['maximum_request_number'] = 3
                os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Reset recommended number complete.\n".encode())
                st.toast("Parameters have been reset.")
                time.sleep(0.5)
                st.rerun()


def model_type_select():
    st.session_state['model_type'] = st.session_state.model_type_select


def temp_slider():
    st.session_state['temperature'] = st.session_state.temperature_slider


def top_p_slider():
    st.session_state['top_p'] = st.session_state.top_p_slider


def presence_penalty_slider():
    st.session_state['presence_penalty'] = st.session_state.presence_penalty_slider


def frequency_penalty_slider():
    st.session_state['frequency_penalty'] = st.session_state.frequency_penalty_slider


def model_params_setting():
    st.header("Model Parameters", help="""By adjusting these parameters, you can control how the assistant behaves, 
                                       such as interaction style and creativity.""")
    st.selectbox(
        label="Model Type",
        options=["gpt-4o-mini", "gpt-4o"],
        index=0,
        help="""The model type determines the model's size and capabilities. 
                The gpt-4o-mini model is a smaller model that runs faster, while the gpt-4o model is larger and more powerful.""",
        key='model_type_select',
        on_change=model_type_select,
    )
    st.slider(
        label="Temperature",
        min_value=0.0,
        max_value=2.0,
        value=st.session_state['temperature'],
        step=0.1,
        help="""The temperature setting controls the randomness of the output: higher values increase randomness, while lower values, especially closer to 0, result in more predictable outputs. 
                It is suggested to adjust either this setting or top_p, but not both at the same time.""",
        key='temperature_slider',
        on_change=temp_slider,
    )
    st.slider(
        label="Top P",
        min_value=0.0,
        max_value=2.0,
        value=st.session_state['top_p'],
        step=0.1,
        help="""Top-p sampling focuses on the model's top predictions that make up the top_p percentage of the total probability. 
                For example, a top-p value of 0.1 refers to the model only considers tokens within the top 10% of the probability mass.""",
        key='top_p_slider',
        on_change=top_p_slider,
    )
    st.slider(
        label="Presence Penalty",
        min_value=-2.0,
        max_value=2.0,
        value=st.session_state['presence_penalty'],
        step=0.1,
        help="""Positive values penalize new tokens based on whether they already appear in the generated text,
                 which may encourage the model to explore new topics.""",
        key='presence_penalty_slider',
        on_change=presence_penalty_slider,
    )
    st.slider(
        label="Frequency Penalty",
        min_value=-2.0,
        max_value=2.0,
        value=st.session_state['frequency_penalty'],
        step=0.1,
        help="""Positive values penalize new tokens based on their existing frequency in the generated text, 
                which may reduce the model's likelihood to repeat the same phrases.""",
        key='frequency_penalty_slider',
        on_change=frequency_penalty_slider,
    )
    st.caption("[More Infor about model's parameters](https://platform.openai.com/docs/api-reference/completions/create)")


def create_sidebar():
    init_sidebar()
    os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Creating sidebar...\n".encode())
    with st.sidebar:
        add_logo()

        set_col, help_col, logout_col = st.columns([1, 1, 1])
        with set_col:
            if st.button("Set", use_container_width=True, key="set_api"):
                st.session_state.current_page = "set_api_page"
        with help_col:
            if st.button("Help", use_container_width=True, key="help"):
                st.session_state.current_page = "help_page"
        with logout_col:
            if st.button("Logout", use_container_width=True, key="logout"):
                st.session_state['logged_in'] = False
                st.session_state["app_init_complete"] = False

                os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Logout.\n".encode())
                os.write(1, f"{'-'*80} \n".encode())
                st.rerun()

        model_params_setting()

    if st.session_state.current_page == "set_api_page":
        os.write(1, f"[{datetime.now().strftime('%H:%M:%S')}] Set API Key.\n".encode())
        set_api_key()
        # set_recommended_number()

    if st.session_state.current_page == "help_page":
        show_help()


if __name__ == "__main__":
    create_sidebar()
