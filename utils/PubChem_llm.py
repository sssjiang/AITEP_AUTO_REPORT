import requests
import pandas as pd
import time
import json
import llm_utils
# API请求函数
def get_cid_by_keyword(keyword):
    """
    使用PubChem API，通过关键词查询CID
    :param keyword: 化学物质的名称或关键词
    :return: 返回CID列表（如果有多个匹配结果），否则返回None
    """
    base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    endpoint = f"/compound/name/{keyword}/cids/JSON"
    url = base_url + endpoint

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("IdentifierList", {}).get("CID", None)
    except requests.exceptions.RequestException as e:
        print(f"CID请求失败: {e}")
        return None
def get_sid_by_keyword(keyword):
    """
    使用PubChem API，通过关键词查询SID
    :param keyword: 化学物质的名称或关键词
    :return: 返回SID列表
    """
    base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    endpoint = f"/substance/name/{keyword}/sids/JSON"
    url = base_url + endpoint

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("IdentifierList", {}).get("SID", None)
    except requests.exceptions.RequestException as e:
        print(f"SID请求失败: {e}")
        return None
def get_compound_data_by_cid(cid):
    """
    使用PubChem API，通过CID查询化学物质的详细信息
    :param cid: 化学物质的CID
    :return: 返回化学物质的详细信息（JSON格式）
    """
    base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound"
    endpoint = f"/{cid}/JSON"
    url = base_url + endpoint

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"CID数据请求失败: {e}")
        return None
def get_substance_data_by_sid(sid):
    """
    使用PubChem API，通过SID查询物质的详细信息
    :param sid: 物质的SID
    :return: 返回物质的详细信息（JSON格式）
    """
    base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/substance"
    endpoint = f"/{sid}/JSON"
    url = base_url + endpoint

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"SID数据请求失败: {e}")
        return None
# 提取类函数 需要的部分，整个json内容太多了
def extract_need_part_cid(data):
    """
    从PubChem API返回的数据中提取需要的部分
    
    :param data: PubChem API返回的JSON格式数据
    :return: 包含需要部分的字典
    """
    data_dict = {}
    try:
        # 获取Record下的Section列表
        sections = data.get('Record', {}).get('Section', [])
        
        # 获取"Names and Identifiers" section
        for section in sections:
            if section.get('TOCHeading') == "Names and Identifiers":
                data_dict["Names and Identifiers"] = section.get('Section', [])
            if section.get('TOCHeading') == "Chemical and Physical Properties":
                data_dict["Chemical and Physical Properties"] = section.get('Section', [])
            # if section.get('TOCHeading') == "Drug and Medication Information":
            #     data_dict["Drug and Medication Information"] = section.get('Section', [])
            # if section.get('TOCHeading') == "Pharmacology and Biochemistry":
            #     data_dict["Pharmacology and Biochemistry"] = section.get('Section', [])
        return data_dict

    except Exception as e:
        print(f"从pubchem中提取需要部分时发生错误: {e}")
        return None


ai = llm_utils.AITEP()
# 单个:化合物入口函数 
prompt="""
Content Start
```json
{{RESULTS}}
```
Content End

Based on the search results in JSON format above, extract the basic information for drug name (`drug_name`). Only include fields with actual values; use empty strings or empty arrays for missing information.

Input:
- `drug_name`: {{DRUG_NAME}}

Expected output format:
```json
{
    "drug_name": "Paracetamol",
    "Synonyms": ["Acetaminophen", "APAP", "Tylenol"],
    "CAS Number": "103-90-2",
    "Molecular Formula": "C8H9NO2",
    "Molecular Weight": "151.16 g/mol",
    "Smiles": "CC(=O)NC1=CC=C(O)C=C1",
    "InchI Key": "RZVAJINKPMORJF-UHFFFAOYSA-N",
    "reference_links": ["https://pubchem.ncbi.nlm.nih.gov/compound/1983"],
    "IUPAC Name": "N-(4-hydroxyphenyl)acetamide",
    "Description": "Analgesic and antipyretic drug used for pain relief and fever reduction",
    "ATC Code": "N02BE01",
    "Pharmacotherapeutic Group": "Analgesics and antipyretics",
    "Appearance": "White crystalline powder",
    "Solubility": "Slightly soluble in water (14 mg/mL at 25°C)"
}
```
"""
def process_chemical(name, apid=None):
    """
    处理单个化学物质，获取其CID/SID和相关信息
    
    参数:
        name (str): 化学物质名称
        apid (str, optional): 化学物质的APID
        
    返回:
        str: 包含处理结果的JSON字符串
    """
    result = {'status': 'success', 'message': None}
    
    print(f"\n处理化学物质: {name}")
    
    # 首先尝试通过关键词获取CID
    cids = get_cid_by_keyword(str(name))
    
    if cids:
        cid = cids[0]
        result['ID'] = cid
        result['ID_Type'] = 'CID'
        print(f"使用CID {cid} 查询详细信息...")
        compound_data = get_compound_data_by_cid(cid)
        
        
        if compound_data:
            # 选取部分信息
            filter_content= extract_need_part_cid(compound_data)
            json_string=json.dumps(filter_content)
            formatted_prompt = prompt.replace("{{RESULTS}}", json_string)
            formatted_prompt = formatted_prompt.replace("{{DRUG_NAME}}", name)
            ai_response = ai.run_llm(file_id=None, llm_model="qwen-long", prompt=formatted_prompt)
            result["GAI_original"] = ai_response
            ai_response=ai_response.get("data")
            for key in ai_response.keys():
                if key not in ["status", "message"]:
                    result[key] = ai_response[key]
            result['reference_links'] = f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}"

           
            
          
    else:
        print(f"未找到'{name}'的CID，尝试查询SID...")
        # 如果没有CID，尝试获取SID
        sids = get_sid_by_keyword(str(name))
        if sids:
            sid = sids[0]
            result['ID'] = sid
            result['ID_Type'] = 'SID'
            print(f"使用SID {sid} 查询详细信息...")
           
            substance_data = get_substance_data_by_sid(sid)
            if substance_data:
                json_string=json.dumps(substance_data)
                formatted_prompt = prompt.replace("{{RESULTS}}", json_string)
                formatted_prompt = formatted_prompt.replace("{{DRUG_NAME}}", name)
                ai_response = ai.run_llm(file_id=None, llm_model="qwen-long", prompt=formatted_prompt)
                result["GAI_original"] = ai_response
                ai_response=ai_response.get("data")
                for key in ai_response.keys():
                    if key not in ["status", "message"]:
                        result[key] = ai_response[key]

                result['reference_links'] = f"https://pubchem.ncbi.nlm.nih.gov/substance/{sid}"
                
                
                
        else:
            print(f"未找到'{name}'的任何CID或SID信息")
            result['status'] = 'error'
            result['message'] = 'no found CID or SID in PubChem'
    
    # 统一返回JSON字符串
    return json.dumps(result, ensure_ascii=False)

if __name__ == "__main__":

    # name="aspirin"
    name="Myrtol"
    print(process_chemical(name))
    #file_path = "chemicals.xlsx"
