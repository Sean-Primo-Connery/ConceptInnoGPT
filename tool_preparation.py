import streamlit as st
from langchain_community.vectorstores.faiss import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from datasets import Dataset
from langchain.output_parsers import StructuredOutputParser, PydanticOutputParser, ResponseSchema
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from pydantic import BaseModel
from typing import List
import math
from sklearn.preprocessing import StandardScaler
from lightgbm import LGBMClassifier
from joblib import load
import numpy as np
import json


def compute_feature(_edge_tuple, _cpc_dict):
    _src = _edge_tuple[0]
    _dst = _edge_tuple[1]
    _src_neigh = set(_cpc_dict[_src])
    _dst_neigh = set(_cpc_dict[_dst])
    _z_list = _src_neigh & _dst_neigh

    cn = len(_z_list)
    jc = cn / len(_src_neigh | _dst_neigh) if len(_src_neigh | _dst_neigh) != 0 else 0
    ss = 2 * cn / (len(_src_neigh) + len(_dst_neigh)) if len(_src_neigh) + len(_dst_neigh) != 0 else 0
    st_ = cn / math.sqrt(len(_src_neigh) * len(_dst_neigh)) if len(_src_neigh) * len(_dst_neigh) != 0 else 0
    hp = cn / min(len(_src_neigh), len(_dst_neigh)) if min(len(_src_neigh), len(_dst_neigh)) != 0 else 0
    hd = cn / max(len(_src_neigh), len(_dst_neigh)) if max(len(_src_neigh), len(_dst_neigh)) != 0 else 0
    lhn = cn / len(_src_neigh) * len(_dst_neigh) if len(_src_neigh) * len(_dst_neigh) != 0 else 0
    pa = len(_src_neigh) * len(_dst_neigh)

    aa = 0
    ra = 0
    if _z_list:
        for _z in _z_list:
            aa += 1 / math.log(len(_cpc_dict[_z])) if len(_cpc_dict[_z]) > 1 else 0
            ra += 1 / len(_cpc_dict[_z])

    return cn, jc, ss, st_, hp, hd, lhn, pa, aa, ra


def pre_vs():
    VS_CPC_Path = "data/cpc_interpretation"
    VS_Title_Path = "data/title_patent"
    VS_Abstract_Path = "data/abstract_patent"

    embedding_model = OpenAIEmbeddings(
        model='text-embedding-3-large',
        dimensions=1024,
        api_key=st.session_state['api_key'],
        base_url=st.session_state['base_url'],
    )

    VS_CPC = FAISS.load_local(VS_CPC_Path, embedding_model, allow_dangerous_deserialization=True)
    VS_Title = FAISS.load_local(VS_Title_Path, embedding_model, allow_dangerous_deserialization=True)
    VS_Abstract = FAISS.load_local(VS_Abstract_Path, embedding_model, allow_dangerous_deserialization=True)

    st.session_state["tool_preparation"]["cpc_vs"] = VS_CPC
    st.session_state["tool_preparation"]["title_vs"] = VS_Title
    st.session_state["tool_preparation"]["abstract_vs"] = VS_Abstract


def pre_patent_cpc_mapping():
    patent_data = Dataset.load_from_disk("data/PatentDataset")
    patent_cpc = {patent: cpc for patent, cpc in zip(patent_data['Publication Number'], patent_data['CPC'])}
    st.session_state["tool_preparation"]["patent_cpc_map"] = patent_cpc

    cpc_patent = {}
    for patent, cpc in patent_cpc.items():
        for c in cpc:
            if c not in cpc_patent:
                cpc_patent[c] = []
            cpc_patent[c].append(patent)
    st.session_state["tool_preparation"]["cpc_patent_map"] = cpc_patent


def pre_cpc_tree():
    cpc_info = Dataset.load_from_disk("data/CPC_info")
    cpc_tree = {}
    for data in cpc_info:
        cpc_tree[data['symbol']] = {
            'level': data['level'],
            'classification': data['classification'],
            'parent': data['parent'],
            'children': data['children']
        }
    st.session_state["tool_preparation"]['cpc_tree'] = cpc_tree


def pre_all_cpc_list():
    domain_cpc_all = set(Dataset.load_from_disk("data/RawData")[-1]['data'].keys())
    if not st.session_state["tool_preparation"]['cpc_tree']:
        pre_cpc_tree()
    all_cpc = list(domain_cpc_all & set(st.session_state["tool_preparation"]['cpc_tree'].keys()))
    st.session_state["tool_preparation"]['all_cpc_list'] = all_cpc


def pre_cpc_coo_data():
    coo_data = Dataset.load_from_disk("data/RawData")

    def get_all_cpc_data(_cpc_net):
        for _data in _cpc_net:
            if _data['type'] == 'all_input':
                return _data['data']

    st.session_state["tool_preparation"]['cpc_coo_data'] = get_all_cpc_data(coo_data)


def pre_prediction_model():
    st.session_state["tool_preparation"]["prediction_model"] = load("model/lgb_model.joblib")
    st.session_state["tool_preparation"]["scaler"] = load("model/scaler.joblib")


def opportunity_filter(_opportunity_list, _proba_threshold=0.9):
    if not st.session_state["tool_preparation"]['cpc_coo_data']:
        pre_cpc_coo_data()
    _filter_list = []
    for _oppo in _opportunity_list:
        _src = _oppo[0][0]
        _dst = _oppo[0][1]
        _proba = _oppo[1]
        if _dst not in st.session_state["tool_preparation"]["cpc_coo_data"][_src] and _proba > _proba_threshold:
            _filter_list.append((_src, _dst, _proba))
    return _filter_list


def find_parent(_cpc):
    if not st.session_state["tool_preparation"]['cpc_tree']:
        pre_cpc_tree()
    cpc_tree = st.session_state["tool_preparation"]['cpc_tree']
    _parent_list = []
    while cpc_tree[_cpc]['parent'] != 'root':
        _parent_list.append(cpc_tree[_cpc]['parent'])
        _cpc = cpc_tree[_cpc]['parent']
    return _parent_list


def find_common_parent(_parent_src, _parent_dst):
    _co_parent = ""
    for _src in _parent_src:
        for _dst in _parent_dst:
            if _src == _dst:
                _co_parent = _src
                break
        if _co_parent:
            break
    if not _co_parent:
        _co_parent = "root"
    return _co_parent


def pre_cpc_embedding():
    cpc_embedding = Dataset.load_from_disk("data/EmbeddingData")
    cpc_embedding_dict = {}
    for data in cpc_embedding:
        cpc_embedding_dict[data['CPC']] = data['emb']
    st.session_state["tool_preparation"]['cpc_embedding'] = cpc_embedding_dict


def computer_similarity(_cpc_pair):
    # 网络相似度
    cpc_embedding_dict = st.session_state["tool_preparation"]['cpc_embedding']
    _src = _cpc_pair[0]
    _dst = _cpc_pair[1]
    _src_emb = cpc_embedding_dict[_src]
    _dst_emb = cpc_embedding_dict[_dst]
    _cos_sim = np.dot(_src_emb, _dst_emb) / (np.linalg.norm(_src_emb) * np.linalg.norm(_dst_emb))

    # 树相似度
    cpc_tree = st.session_state["tool_preparation"]['cpc_tree']
    _src_level = cpc_tree[_src]['level']
    _dst_level = cpc_tree[_dst]['level']

    _src_parent_list = find_parent(_src)
    _dst_parent_list = find_parent(_dst)
    _common_parent = find_common_parent(_src_parent_list, _dst_parent_list)
    _common_parent_level = cpc_tree[_common_parent]['level'] if _common_parent != "root" else 1

    # Wu-Palmer相似性
    _tree_sim = 2 * _common_parent_level / (_src_level + _dst_level)

    return _cos_sim + 1 - _tree_sim


def explain_cpc_definition(_cpc):
    return st.session_state["tool_preparation"]['cpc_tree'][_cpc]['classification']


def patent_retrieval(_cpc_pair, _similar_patent):
    _src, _dst = _cpc_pair
    patent_cpc = st.session_state["tool_preparation"]["patent_cpc_map"]
    cpc_patent = st.session_state["tool_preparation"]["cpc_patent_map"]

    _src_patent = []
    for _o_p in _similar_patent:
        if _src in patent_cpc[_o_p]:
            _src_patent.append(_o_p)

    _dst_patent = cpc_patent[_dst]

    _src_patent_cpc = {_patent: patent_cpc[_patent] for _patent in _src_patent}
    _dst_patent_cpc = {_patent: patent_cpc[_patent] for _patent in _dst_patent}

    _technical_overlap = []
    for _s_patent in _src_patent_cpc:
        for _d_patent in _dst_patent_cpc:
            s_cpc = _src_patent_cpc[_s_patent]
            d_cpc = _dst_patent_cpc[_d_patent]
            _overlap = set(s_cpc) & set(d_cpc)
            wup = 2 * len(_overlap) / (len(s_cpc) + len(d_cpc)) if len(s_cpc) + len(d_cpc) != 0 else 0
            _technical_overlap.append((_s_patent, _d_patent, wup))

    _technical_overlap = sorted(_technical_overlap, key=lambda x: x[2], reverse=True)
    return _technical_overlap


def pre_llm():
    return ChatOpenAI(
        model=st.session_state['model_type'],
        temperature=st.session_state['temperature'],
        top_p=st.session_state['top_p'],
        presence_penalty=st.session_state['presence_penalty'],
        frequency_penalty=st.session_state['frequency_penalty'],
        api_key=st.session_state['api_key'],
        base_url=st.session_state['base_url']
    )


def cpc_interp(_cpc_list, llm=None):
    CPC_interp_response_schemas = [
        ResponseSchema(
            name="Technology Feature",
            type="str",
            description="Describe the technology feature of this Classification Code in one sentence. Retain only essential details."
        ),
        ResponseSchema(
            name="Functions",
            type="List[str]",
            description="Several phrases describe the functions that the Classification Code can achieve, particularly supporting the Design Requirement."
        ),
        ResponseSchema(
            name="Core Feature",
            type="str",
            description="A phrase that describes the core technology feature of this Classification Code."
        )
    ]
    CPC_interp_output_parser = StructuredOutputParser.from_response_schemas(CPC_interp_response_schemas)
    CPC_interp_format_instructions = CPC_interp_output_parser.get_format_instructions(only_json=True)

    CPC_interp_system_prompt = SystemMessagePromptTemplate.from_template(
        "You are an expert in patent analysis, have a detailed understanding of the CPC patent classification system, and can describe the technology feature of a Classification Code in detailed professional language. You must return a valid JSON format response.")
    CPC_interp_requirement = """
    Task: Comprehensively understand the following Classification Code definition, and professionally and logically describe the technology feature and function of the Classification Code.

    **Classification Code:** {cpc}
    **Definition:** {cpc_definition}
    Note: The symbol "->" indicates a refinement of technology features. For example, if Classification Code 1 is defined as "Technology Feature A -> Technology Feature B", it means that under the condition of Technology Feature A, it is limited to Technology Feature B.
    
    The output should be formatted as a JSON instance that conforms to the JSON schema below.
    {CPC_interp_format_instructions}
    """
    CPC_interp_human_prompt = HumanMessagePromptTemplate.from_template(CPC_interp_requirement)
    CPC_interp_prompt = ChatPromptTemplate.from_messages([CPC_interp_system_prompt, CPC_interp_human_prompt])

    if not llm:
        llm = pre_llm()

    def get_cpc_interp_batch(_cpc_list):
        _cpc_dict_list = []
        for _cpc in _cpc_list:
            _cpc_dict = {
                "cpc": _cpc,
                "cpc_definition": explain_cpc_definition(_cpc),
                "CPC_interp_format_instructions": CPC_interp_format_instructions
            }
            _cpc_dict_list.append(CPC_interp_prompt.invoke(_cpc_dict))
        _interp_list = (llm | CPC_interp_output_parser).batch(_cpc_dict_list)
        return {_cpc: _interp for _cpc, _interp in zip(_cpc_list, _interp_list)}

    return get_cpc_interp_batch(_cpc_list)


def to_interp(_to_list):
    P_CSG_response_schemas = [
        ResponseSchema(
            name="Title",
            type="str",
            description="The title of conceptual solution, describing the core functions and purposes of the solution."
        ),
        ResponseSchema(
            name="Integration",
            type="str",
            description="A brief introduction summarizing the technologies integrated into this solution."
        ),
        ResponseSchema(
            name="Core Functions",
            type="List[str]",
            description="Several phrases that describe the core functions of the conceptual solution."
        ),
        ResponseSchema(
            name="Purposes",
            type="str",
            description="A brief description of the purposes of the conceptual solution."
        )
    ]
    P_CSG_output_parser = StructuredOutputParser.from_response_schemas(P_CSG_response_schemas)
    P_CSG_format_instructions = P_CSG_output_parser.get_format_instructions(only_json=True)

    P_CSG_system_prompt = SystemMessagePromptTemplate.from_template(
        "You are a conceptual design expert specializing in identifying innovation opportunities through the analysis of combined patent Classification Codes. You must return a valid JSON format response.")
    P_CSG_requirement = """
    Task: Analyze the innovation opportunity arising from the technological convergence represented by the two Classification Codes in Technology Convergence Prediction, and develop an innovative conceptual solution that meets the Design Requirement.

    ## Design Requirement
    {requirement}

    ## Technology Convergence Prediction
    Predict that the following two Classification Codes will undergo technology convergence, combining to generate innovation opportunity.
    
    {cpc1}: {cpc1_core_feature}
    technology feature: {cpc1_technology_feature}
    function: {cpc1_technology_feature}
    
    {cpc2}: {cpc2_core_feature}
    technology feature: {cpc2_technology_feature}
    function: {cpc2_technology_feature}
    
    Based on the technologies represented by these two Classification Codes, consider the technological innovations that could result from integrating {cpc2_core_feature} into {cpc1_core_feature}.
    
    The output should be formatted as a JSON instance that conforms to the JSON schema below.
    {P_CSG_format_instructions}
    """
    P_CSG_human_prompt = HumanMessagePromptTemplate.from_template(P_CSG_requirement)
    P_CSG_prompt = ChatPromptTemplate.from_messages([P_CSG_system_prompt, P_CSG_human_prompt])

    llm = pre_llm()

    def get_to_interp_batch(_requirement, _to_list):
        _all_cpc_list = []
        for _to in _to_list:
            _all_cpc_list.extend([_to[0], _to[1]])
        _all_cpc_list = list(set(_all_cpc_list))
        _cpc_interp_dict = cpc_interp(_all_cpc_list)
        st.session_state["tool_preparation"]["to_cpc_interp"] = _cpc_interp_dict

        _to_dict_list = []
        for _to in _to_list:
            _cpc1 = _to[0]
            _cpc2 = _to[1]
            _cpc1_info = _cpc_interp_dict[_cpc1]
            _cpc2_info = _cpc_interp_dict[_cpc2]
            _to_dict = {
                "requirement": _requirement,
                "cpc1": _cpc1,
                "cpc1_core_feature": _cpc1_info["Core Feature"],
                "cpc1_technology_feature": _cpc1_info["Technology Feature"],
                "cpc1_function": _cpc1_info["Functions"],
                "cpc2": _cpc2,
                "cpc2_core_feature": _cpc2_info["Core Feature"],
                "cpc2_technology_feature": _cpc2_info["Technology Feature"],
                "cpc2_function": _cpc2_info["Functions"],
                "P_CSG_format_instructions": P_CSG_format_instructions
            }
            _to_dict_list.append(P_CSG_prompt.invoke(_to_dict))
        _interp_list = (llm | P_CSG_output_parser).batch(_to_dict_list)
        return {_to[:2]: _interp for _to, _interp in zip(_to_list, _interp_list)}

    return get_to_interp_batch(st.session_state["conceptual_solution_info"]["requirement"], _to_list)


def pre_tfa():
    TFA_response_schemas = [
        ResponseSchema(
            name="Core Function",
            type="List[str]",
            description="Several phrases that describe the core functions of the classification code, particularly supporting the conceptual solution. Retain only essential details."
        )
    ]
    TFA_output_parser = StructuredOutputParser.from_response_schemas(TFA_response_schemas)
    TFA_format_instructions = TFA_output_parser.get_format_instructions(only_json=True)

    TFA_system_prompt = SystemMessagePromptTemplate.from_template(
        "You are a technical analysis expert responsible for analyzing the functions of the Classification Code that support the implementation of the Conceptual Solution.  You must return a valid JSON format response.")
    TFA_requirement = """
    Task: Analyze the core functions of the Classification Code in the Conceptual Solution.

    ## Design Requirement
    {requirement}

    ## Conceptual Solution
    {conceptual_solution}

    ## Classification Code
    {cpc}: {cpc_core_feature}
    function: {cpc_function}
    
    The output should be formatted as a JSON instance that conforms to the JSON schema below.
    {TFA_format_instructions}
    """
    TFA_human_prompt = HumanMessagePromptTemplate.from_template(TFA_requirement)
    TFA_prompt = ChatPromptTemplate.from_messages([TFA_system_prompt, TFA_human_prompt])

    return TFA_format_instructions, TFA_prompt, TFA_output_parser


def pre_cso():
    CSO_response_schemas = [
        ResponseSchema(
            name="Title",
            type="str",
            description="A concise title that summarizes the Conceptual Solution, providing a clear overview of the solution's core functions and purposes."
        ),
        ResponseSchema(
            name="Function Modules",
            type="List[str]",
            description="Several phrases that describe the core function modules of the conceptual solution, with 2-5 functional modules."
        ),
        ResponseSchema(
            name="Purpose",
            type="str",
            description="A brief description of the purposes and the innovativeness of the conceptual solution."
        ),
    ]
    CSO_output_parser = StructuredOutputParser.from_response_schemas(CSO_response_schemas)
    CSO_format_instructions = CSO_output_parser.get_format_instructions(only_json=True)

    CSO_system_prompt = SystemMessagePromptTemplate.from_template(
        "You are a conceptual design expert who develops innovative conceptual solutions. You must return a valid JSON format response.")
    CSO_requirement = """
    Task: Consider the support of Relevant Technologies for the Preliminary Conceptual Solution and develop a professional and innovative conceptual solution.

    ## Design Requirement
    {requirement}

    ## Preliminary Conceptual Solution
    {preliminary_conceptual_solution}

    ## Relevant Technologies
    {relevant_technologies}
    
    The output should be formatted as a JSON instance that conforms to the JSON schema below.
    {CSO_format_instructions}
    """
    CSO_human_prompt = HumanMessagePromptTemplate.from_template(CSO_requirement)
    CSO_prompt = ChatPromptTemplate.from_messages([CSO_system_prompt, CSO_human_prompt])

    return CSO_format_instructions, CSO_prompt, CSO_output_parser


def pre_fmd():
    class FunctionalModule(BaseModel):
        module_name: str
        description: str
        applied_technologies: List[str]

    class FunctionalModulesResponse(BaseModel):
        functional_modules: List[FunctionalModule]

    FMD_output_parser = PydanticOutputParser(pydantic_object=FunctionalModulesResponse)
    FMD_format_instructions = FMD_output_parser.get_format_instructions()

    FMD_system_prompt = SystemMessagePromptTemplate.from_template(
        "You are a conceptual design expert specializing in designing functional modules required for Conceptual Solutions. You must return a valid JSON format response.")
    FMD_requirement = """
    Task: Design the functional modules of the Conceptual Solution.

    ## Design Requirement
    {requirement}

    ## Conceptual Solution
    {conceptual_solution}

    ## Relevant Technologies
    {relevant_technologies}

    Analyze the mapping relationship between Relevant Technologies and the Function Modules in Conceptual Solution, and design Function Modules that meet the Design Requirement. Maximize the utilization of all technologies listed in Relevant Technologies.
    For each module, provide:
    - **Module Name**: The name of the functional module.
    - **Description**: A detailed description of the functional module, including the working principles, functions, and purposes of the module. 
    - **Applied Technologies**: The List of Relevant Technologies represented by classification codes that are applied in the functional module.
    
    {FMD_format_instructions}
    """
    FMD_human_prompt = HumanMessagePromptTemplate.from_template(FMD_requirement)
    FMD_prompt = ChatPromptTemplate.from_messages([FMD_system_prompt, FMD_human_prompt])

    return FMD_format_instructions, FMD_prompt, FMD_output_parser


def pre_csd():
    CSD_response_schemas = [
        ResponseSchema(
            name="Title",
            type="str",
            description="A concise title that summarizes the Conceptual Solution, providing a clear overview of the solution's core functions and purposes. Retain only essential details."
        ),
        ResponseSchema(
            name="Description",
            type="str",
            description="A detailed description of the conceptual solution includes an overall functional overview, and the primary functions and purposes of each functional module. Retain only the core details and present the content in a single paragraph."
        )
    ]
    CSD_output_parser = StructuredOutputParser.from_response_schemas(CSD_response_schemas)
    CSD_format_instructions = CSD_output_parser.get_format_instructions(only_json=True)

    CSD_system_prompt = SystemMessagePromptTemplate.from_template(
        "You are a conceptual design expert who optimizes and adjusts conceptual solutions by analyzing the descriptions of functional modules, ensuring logical coherence and professional articulation. You must return a valid JSON format response.")
    CSD_requirement = """
    Task: Analyze the roles of each Functional Module based on the Design Requirement, and reorganize the Initial Conceptual Solution.

    ## Design Requirement
    {requirement}

    ## Functional Modules
    {functional_modules}

    ## Initial Conceptual Solution
    {initial_conceptual_solution}
    
    The output should be formatted as a JSON instance that conforms to the JSON schema below.
    {CSD_format_instructions}
    """
    CSD_human_prompt = HumanMessagePromptTemplate.from_template(CSD_requirement)
    CSD_prompt = ChatPromptTemplate.from_messages([CSD_system_prompt, CSD_human_prompt])

    return CSD_format_instructions, CSD_prompt, CSD_output_parser


def cs_generate(_oppo_pair, _overlap_cpc_comb, _cpc_interp, _requirement, _pcs, _model_info):
    TFA_format_instructions, TFA_prompt, TFA_output_parser = pre_tfa()
    CSO_format_instructions, CSO_prompt, CSO_output_parser = pre_cso()
    FMD_format_instructions, FMD_prompt, FMD_output_parser = pre_fmd()
    CSD_format_instructions, CSD_prompt, CSD_output_parser = pre_csd()

    with open(_model_info, "r") as f:
        _model_info_dict = json.load(f)
    llm = ChatOpenAI(
        model=_model_info_dict['model_type'],
        temperature=_model_info_dict['temperature'],
        top_p=_model_info_dict['top_p'],
        presence_penalty=_model_info_dict['presence_penalty'],
        frequency_penalty=_model_info_dict['frequency_penalty'],
        api_key=_model_info_dict['api_key'],
        base_url=_model_info_dict['base_url']
    )

    # 技术作用分析
    def get_pcs_info(_cs):
        _pcs_info = ""
        _pcs_info += _cs['Title'] + "\n" + 'Integration: ' + _cs['Integration'] + "\n" + 'Core Functions: ' + "; ".join(
            _cs['Core Functions']) + '\n' + 'Purposes: ' + _cs['Purposes'] + "\n"
        return _pcs_info

    def get_cpc_cf_batch(_requirement, _cpc_interp_dict, _cs):
        _cs_info = get_pcs_info(_cs)
        _cf_dict_list = []
        _cpc_list = []
        for _cpc, _cpc_info in _cpc_interp_dict.items():
            _CF_dict = {
                "requirement": _requirement,
                "cpc": _cpc,
                "cpc_core_feature": _cpc_info['Core Feature'],
                "cpc_function": "; ".join(_cpc_info['Functions']),
                "conceptual_solution": _cs_info,
                "TFA_format_instructions": TFA_format_instructions
            }
            _cf_dict_list.append(TFA_prompt.invoke(_CF_dict))
            _cpc_list.append(_cpc)
        _cf_list = (llm | TFA_output_parser).batch(_cf_dict_list)
        return {_cpc: _cf['Core Function'] for _cpc, _cf in zip(_cpc_list, _cf_list)}

    # 概念方案完善
    CSO_chain = CSO_prompt | llm | CSO_output_parser

    def generate_relevant_cpc_tf_info(_cpc_tf_dict):
        _relevant_cpc_tf_info_ = ""
        for _cpc_, _tf in _cpc_tf_dict.items():
            _relevant_cpc_tf_info_ += _cpc_ + ": " + '; '.join(_tf) + "\n"
        return _relevant_cpc_tf_info_

    def get_cso(_requirement, _pcs, _relevant_cpc_tf_info):
        _pcs_info = get_pcs_info(_pcs)
        _CSO_dict = {
            "requirement": _requirement,
            "preliminary_conceptual_solution": _pcs_info,
            "relevant_technologies": _relevant_cpc_tf_info,
            "CSO_format_instructions": CSO_format_instructions
        }
        return CSO_chain.invoke(_CSO_dict)

    # 功能模块设计
    FMD_chain = FMD_prompt | llm | FMD_output_parser

    def get_cs_info(_cs):
        _cs_info = ""
        _cs_info += _cs['Title'] + "\n" + 'Function Modules: ' + "; ".join(
            _cs['Function Modules']) + '\n' + 'Purpose: ' + _cs['Purpose'] + "\n"
        return _cs_info

    # noinspection PyTypeChecker
    def get_fmd(_requirement, _cs, _relevant_cpc_ct_info):
        _cs_info = get_cs_info(_cs)
        _FMD_dict = {
            "requirement": _requirement,
            "conceptual_solution": _cs_info,
            "relevant_technologies": _relevant_cpc_ct_info,
            "FMD_format_instructions": FMD_format_instructions
        }
        _FMD = FMD_chain.invoke(_FMD_dict)
        return [dict(_f) for _f in dict(_FMD)['functional_modules']]

    # 概念方案调整
    CSD_chain = CSD_prompt | llm | CSD_output_parser

    def get_fm_info(_fm):
        _fm_info = ""
        _mark = 1
        for _f in _fm:
            _fm_info += f"Functional Module {_mark}: \n"
            _fm_info += "Module Name: " + _f['module_name'] + "\n"
            _fm_info += "Applied Technologies: " + '; '.join(_f['applied_technologies']) + "\n"
            _fm_info += "Description: " + _f['description'] + "\n"
            _mark += 1
        return _fm_info

    def get_csd(_requirement, _fm, _cs):
        _fm_info = get_fm_info(_fm)
        _cs_info = get_cs_info(_cs)
        _CSD_dict = {
            "requirement": _requirement,
            "functional_modules": _fm_info,
            "initial_conceptual_solution": _cs_info,
            "CSD_format_instructions": CSD_format_instructions
        }
        return CSD_chain.invoke(_CSD_dict)

    # 整体流程
    _all_cpc_cf = get_cpc_cf_batch(_requirement, _cpc_interp, _pcs)

    _relevant_cpc_tf_info = generate_relevant_cpc_tf_info(_all_cpc_cf)
    _cso = get_cso(_requirement, _pcs, _relevant_cpc_tf_info)

    _fmd = get_fmd(_requirement, _cso, _relevant_cpc_tf_info)

    _csd = get_csd(_requirement, _fmd, _cso)

    cs_info_dict = {
        "Title": _csd['Title'],
        "Description": _csd['Description'],
        "Functional Modules": _fmd
    }

    return cs_info_dict


def re_generate_fm(_func_cpc):
    RFM_response_schemas = [
        ResponseSchema(
            name="module_name",
            type="str",
            description="A concise module name that highlights its primary function and purpose."
        ),
        ResponseSchema(
            name="description",
            type="str",
            description="A detailed description of the functional module. Describe the working principle of the function module in no more than three sentences, followed by two sentences respectively describing its function and purpose."
        )
    ]
    RFM_output_parser = StructuredOutputParser.from_response_schemas(RFM_response_schemas)
    RFM_format_instructions = RFM_output_parser.get_format_instructions(only_json=True)

    RFM_system_prompt = SystemMessagePromptTemplate.from_template(
        "You are a technical analyst responsible for designing functional module. You must return a valid JSON format response.")
    RFM_requirement = """
        Task: Design a functional module.

        ## Design Requirement
        {requirement}
        
        ## Classification Codes
        {classification_code_info}

        ## Conceptual Solution
        {conceptual_solution}
        
        Complete the module design according to the following steps:
        1. Analyze the functions that can be achieved by the combinations of all technologies within the Classification Codes, particularly identifying which Core Function or combinations of Core Functions of the Conceptual Solution can be realized.
        2. Design a functional module and provide its Name and Description as per the subsequent requirements.
        3. Describe the functional module in a single natural paragraph.
        4. The output should be formatted as a JSON instance that conforms to the JSON schema below.
        {TFA_format_instructions}
        """
    RFM_human_prompt = HumanMessagePromptTemplate.from_template(RFM_requirement)
    RFM_prompt = ChatPromptTemplate.from_messages([RFM_system_prompt, RFM_human_prompt])

    llm = pre_llm()

    RFM_chain = RFM_prompt | llm | RFM_output_parser

    def get_cs_info():
        selected_to = st.session_state["conceptual_solution_info"]["technology_opportunity"]
        all_cs_info = st.session_state['technology_opportunity_all']
        cs_info_text = f"Title: {all_cs_info[selected_to]['Title']}\n"
        cs_info_text += f"Description: {all_cs_info[selected_to]['Integration']}\n"
        return cs_info_text

    def get_classification_code_info(_func_cpc):
        _cpc_interp = st.session_state["tool_preparation"]["cs_cpc_interp"]
        cpc_info = ""
        for _cpc in _func_cpc:
            cpc_info += f"{_cpc}: {_cpc_interp[_cpc]['Core Feature']}\n"
            cpc_info += f"Technology Feature: {_cpc_interp[_cpc]['Technology Feature']}\n"
            cpc_info += f"Function: {'; '.join(_cpc_interp[_cpc]['Functions'])}\n".replace(".", "")
        return cpc_info

    def get_rfm(_func_cpc):
        _cs_info = get_cs_info()
        _cpc_info = get_classification_code_info(_func_cpc)
        _RFM_dict = {
            "requirement": st.session_state["conceptual_solution_info"]["requirement"],
            "conceptual_solution": _cs_info,
            "classification_code_info": _cpc_info,
            "TFA_format_instructions": RFM_format_instructions
        }
        return RFM_chain.invoke(_RFM_dict)

    return get_rfm(_func_cpc)


def re_generate_cs(_func_modules):
    RCS_response_schemas = [
        ResponseSchema(
            name="Title",
            type="str",
            description="A concise title that summarizes the Conceptual Solution, providing a clear overview of the solution's core functions and purposes. Retain only essential details."
        ),
        ResponseSchema(
            name="Description",
            type="str",
            description="A detailed description of the conceptual solution includes an overall functional overview, and the primary functions and purposes of each functional module. Retain only the core details and present the content in a single paragraph."
        )
    ]
    RCS_output_parser = StructuredOutputParser.from_response_schemas(RCS_response_schemas)
    RCS_format_instructions = RCS_output_parser.get_format_instructions(only_json=True)

    RCS_system_prompt = SystemMessagePromptTemplate.from_template(
        "You are a conceptual design expert responsible for generating the conceptual solution title and overall descriptions based on the functional module descriptions. You must return a valid JSON format response.")
    RCS_requirement = """
        Task: Based on the following functional module description, generate a conceptual solution title and an overall description. Pay attention to the Design Requirement and Technology Opportunity, as they form the background information for the conceptual solution.

        ## Functional Modules
        {functional_modules}

        ## Design Requirement
        {requirement}

        ## Technology Opportunity
        {technology_opportunity}

        The output should be formatted as a JSON instance that conforms to the JSON schema below.
        {CSD_format_instructions}
        """
    RCS_human_prompt = HumanMessagePromptTemplate.from_template(RCS_requirement)
    RCS_prompt = ChatPromptTemplate.from_messages([RCS_system_prompt, RCS_human_prompt])

    llm = pre_llm()

    RCS_chain = RCS_prompt | llm | RCS_output_parser

    def get_fm_info(_func_modules):
        _fm_info = ""
        _mark = 1
        for _f in _func_modules:
            _fm_info += f"Functional Module {_mark}: \n"
            _fm_info += "Module Name: " + _f['module_name'] + "\n"
            _fm_info += "Applied Technologies: " + '; '.join(_f['applied_technologies']) + "\n"
            _fm_info += "Description: " + _f['description'] + "\n\n"
            _mark += 1
        return _fm_info

    def get_to_info():
        _to_info = ""
        selected_to = st.session_state["conceptual_solution_info"]["technology_opportunity"]
        all_cs_info = st.session_state['technology_opportunity_all']
        _to_info += f"Title: {all_cs_info[selected_to]['Title']}\n"
        _to_info += f"Description: {all_cs_info[selected_to]['Integration']}\n"
        _to_info += f"Purposes: {all_cs_info[selected_to]['Purposes']}\n"
        return _to_info

    def get_csd(_requirement, _fm):
        _fm_info = get_fm_info(_fm)
        _to_info = get_to_info()
        _CSD_dict = {
            "requirement": _requirement,
            "functional_modules": _fm_info,
            "technology_opportunity": _to_info,
            "CSD_format_instructions": RCS_format_instructions
        }
        return RCS_chain.invoke(_CSD_dict)

    return get_csd(st.session_state["conceptual_solution_info"]["requirement"], _func_modules)


if __name__ == "__main__":
    pre_vs()
