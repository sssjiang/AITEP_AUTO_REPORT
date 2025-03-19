import requests
import pandas as pd
import time
import json
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
# 提取类函数
def extract_first_cas(data):
    """
    从PubChem API返回的数据中提取第一个CAS Number
    
    :param data: PubChem API返回的JSON格式数据
    :return: 第一个CAS Number或None
    """
    try:
        # 获取Record下的Section列表
        sections = data.get('Record', {}).get('Section', [])
        
        # 查找"Names and Identifiers" section
        for section in sections:
            if section.get('TOCHeading') == "Names and Identifiers":
                # 在子Section中查找"Other Identifiers"
                for subsection in section.get('Section', []):
                    if subsection.get('TOCHeading') == "Other Identifiers":
                        # 在Information中查找CAS

                        subsubsection= subsection.get('Section', [])
                        for info in subsubsection:
                            if info.get('TOCHeading') == "CAS":
                                # 获取StringWithMarkup中的第一个String值
                                string_with_markup = info.get('Information', {})[0].get('Value', []).get('StringWithMarkup', [])
                                print(string_with_markup)
                                if string_with_markup:
                                    return string_with_markup[0].get('String')
        return None

    except Exception as e:
        print(f"提取CAS Number时发生错误: {e}")
        return None
def extract_Weight(data):
    """提取Molecular Weight"""
    try:
        sections = data.get('Record', {}).get('Section', [])
        for section in sections:
            if section.get('TOCHeading') == "Chemical and Physical Properties":
                for subsection in section.get('Section', []):
                    if subsection.get('TOCHeading') == "Computed Properties":
                        subsubsection= subsection.get('Section', [])
                        for info in subsubsection:
                            if info.get('TOCHeading') == "Molecular Weight":
                                 # 获取StringWithMarkup中的第一个String值
                                string_with_markup = info.get('Information', {})[0].get('Value', []).get('StringWithMarkup', [])
                                print(string_with_markup)
                                if string_with_markup:
                                    return string_with_markup[0].get('String')
                                 
        return None
    except Exception as e:
        print(f"提取SMILES时发生错误: {e}")
        return None
def extract_Formular(data):
    """提取Molecular Weight"""
    try:
        sections = data.get('Record', {}).get('Section', [])
        for section in sections:
            if section.get('TOCHeading') == "Chemical and Physical Properties":
                for subsection in section.get('Section', []):
                    if subsection.get('TOCHeading') == "Computed Properties":
                        subsubsection= subsection.get('Section', [])
                        for info in subsubsection:
                            if info.get('TOCHeading') == "Molecular Formula":
                                 # 获取StringWithMarkup中的第一个String值
                                string_with_markup = info.get('Information', {})[0].get('Value', []).get('StringWithMarkup', [])
                                print(string_with_markup)
                                if string_with_markup:
                                    return string_with_markup[0].get('String')
                                

                             
        return None
    except Exception as e:
        print(f"提取SMILES时发生错误: {e}")
        return None   
def extract_Molecular_Formula(data):
    """提取Molecular Formula"""
    try:
        sections = data.get('Record', {}).get('Section', [])
        for section in sections:
            if section.get('TOCHeading') == "Names and Identifiers":
                subsections = section.get('Section', [])
                for subsection in subsections:
                    if subsection.get('TOCHeading') == "Molecular Formula":
                        information = subsection.get('Information', [])
                        if information:
                            # 获取StringWithMarkup中的第一个String值
                            string_with_markup = information[0].get('Value', {}).get('StringWithMarkup', [])
                            if string_with_markup:
                                return string_with_markup[0].get('String')
        return None
    except Exception as e:
        print(f"提取Molecular Formula时发生错误: {e}")
        return None
def extract_Smiles(data):
    """提取SMILES"""
    try:
        sections = data.get('Record', {}).get('Section', [])
        for section in sections:
            if section.get('TOCHeading') == "Names and Identifiers":
                for subsection in section.get('Section', []):
                    if subsection.get('TOCHeading') == "Computed Descriptors":
                        subsubsection= subsection.get('Section', [])
                        for info in subsubsection:
                            if info.get('TOCHeading') == "SMILES":
                                 # 获取StringWithMarkup中的第一个String值
                                string_with_markup = info.get('Information', {})[0].get('Value', []).get('StringWithMarkup', [])
                                print(string_with_markup)
                                if string_with_markup:
                                    return string_with_markup[0].get('String')
                                 
        return None
    except Exception as e:
        print(f"提取SMILES时发生错误: {e}")
        return None
def extract_synonyms(data):
    """提取Synonyms"""
    try:
        sections = data.get('Record', {}).get('Section', [])
        for section in sections:
            if section.get('TOCHeading') == "Names and Identifiers":
                for subsection in section.get('Section', []):
                    if subsection.get('TOCHeading') == "Synonyms":
                        # 获取所有Synonyms
                        subsection=subsection.get('Section', [])
                        # 如果subsection是一个列表取第一个
                        if isinstance(subsection, list):
                            subsection_1 = subsection[0]
                        else:
                            subsection_1 = subsection
                        synonyms = []
                        infos=subsection_1.get('Information', [])
                        for info in infos: 
                            # 获取StringWithMarkup中的所有String值
                            string_with_markup = info.get('Value', {}).get('StringWithMarkup', [])
                            for string in string_with_markup:
                                synonyms.append(string.get('String'))
                        # 取前10个Synonyms
                        return synonyms[:10]
        return None
    except Exception as e:
        print(f"提取Synonyms时发生错误: {e}")
        return None
def extract_InchI_Key(data):
    """提取InchI Key"""
    try:
        sections = data.get('Record', {}).get('Section', [])
        for section in sections:
            if section.get('TOCHeading') == "Names and Identifiers":
                for subsection in section.get('Section', []):
                    if subsection.get('TOCHeading') == "Computed Descriptors":
                        subsubsection= subsection.get('Section', [])
                        for info in subsubsection:
                            if info.get('TOCHeading') == "InChIKey":
                                 # 获取StringWithMarkup中的第一个String值
                                string_with_markup = info.get('Information', {})[0].get('Value', []).get('StringWithMarkup', [])
                                print(string_with_markup)
                                if string_with_markup:
                                    return string_with_markup[0].get('String')
                                 
        return None
    except Exception as e:
        print(f"提取InchI Key时发生错误: {e}")
        return None
def extract_IUPAC_Name(data):
    """提取IUPAC Name"""
    try:
        sections = data.get('Record', {}).get('Section', [])
        for section in sections:
            if section.get('TOCHeading') == "Names and Identifiers":
                for subsection in section.get('Section', []):
                    if subsection.get('TOCHeading') == "Computed Descriptors":
                        subsubsection= subsection.get('Section', [])
                        for info in subsubsection:
                            if info.get('TOCHeading') == "IUPAC Name":
                                 # 获取StringWithMarkup中的第一个String值
                                string_with_markup = info.get('Information', {})[0].get('Value', []).get('StringWithMarkup', [])
                                print(string_with_markup)
                                if string_with_markup:
                                    return string_with_markup[0].get('String')
                                 
        return None
    except Exception as e:
        print(f"提取InchI Key时发生错误: {e}")
        return None


def extract_ATC_Code(data):
    """提取ATC Code"""
    try:
        sections = data.get('Record', {}).get('Section', [])
        for section in sections:
            if section.get('TOCHeading') == "Pharmacology and Biochemistry":
                for subsection in section.get('Section', []):
                    if subsection.get('TOCHeading') == "ATC Code":
                        # 获取所有ATC Codes
                        atc_codes = []
                        for info in subsection.get('Information', []):
                            atc_codes.append(info.get('Value', {}).get('StringWithMarkup', [])[0].get('String'))
                        return atc_codes[0]
        return None
    except Exception as e:
        print(f"提取ATC Code时发生错误: {e}")
        return None

# 单个:化合物入口函数 


def process_chemical(name, apid=None):
    """
    处理单个化学物质，获取其CID/SID和相关信息
    
    参数:
        name (str): 化学物质名称
        apid (str, optional): 化学物质的APID
        
    返回:
        str: 包含处理结果的JSON字符串
    """
   
    result={
    'APID': apid, 
    'Name': name,
    'CAS Number':"",
    'Molecular Weight':"",
    'Molecular Formula':"",
    'Smiles':"",
    'Synonyms':"",
    'InchI Key':"",
    'IUPAC Name':"",
    'ATC Code':"",
    'status': 'success',
    'message': "",
    'reference_links': ""
    }
    print(f"\n处理化学物质: {name}")
    
    # 首先尝试通过关键词获取CID
    cids = get_cid_by_keyword(str(name))
    
    if cids:
        cid = cids[0]
        result['ID'] = cid
        result['ID_Type'] = 'CID'
        print(f"使用CID {cid} 查询详细信息...")
        compound_data = get_compound_data_by_cid(cid)
        result['reference_links'] = f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}"
        if compound_data:
            CAS_name = extract_first_cas(compound_data)
            weight = extract_Weight(compound_data)
            formular = extract_Molecular_Formula(compound_data)
            result['CAS Number'] = CAS_name
            result['Molecular Weight'] = weight
            result['Molecular Formula'] = formular
            result['Smiles'] = extract_Smiles(compound_data)
            result['Synonyms'] = extract_synonyms(compound_data)
            result['InchI Key'] = extract_InchI_Key(compound_data)
            result['IUPAC Name'] = extract_IUPAC_Name(compound_data)
            result['ATC Code'] = extract_ATC_Code(compound_data)
            print(f"找到描述: {CAS_name[:100]}..." if CAS_name else "未找到描述CAS")
            print(f"找到描述: {weight[:100]}..." if weight else "未找到描述weight")
            print(f"找到描述: {formular[:100]}..." if formular else "未找到描述formular")
            print(f"找到描述: {result['Smiles'][:100]}..." if result['Smiles'] else "未找到描述Smiles")

    else:
        print(f"未找到'{name}'的CID，尝试查询SID...")
        # 如果没有CID，尝试获取SID
        sids = get_sid_by_keyword(str(name))
        if sids:
            sid = sids[0]
            result['ID'] = sid
            result['ID_Type'] = 'SID'
            print(f"使用SID {sid} 查询详细信息...")
            result['reference_links'] = f"https://pubchem.ncbi.nlm.nih.gov/substance/{sid}"
            substance_data = get_substance_data_by_sid(sid)
            if substance_data:
                CAS_name = extract_first_cas(substance_data)
                result['CAS Number'] = CAS_name
                print(f"找到描述: {CAS_name[:100]}..." if CAS_name else "未找到描述CAS")
                
        else:
            print(f"未找到'{name}'的任何CID或SID信息")
            result['status'] = 'error'
            result['message'] = 'no found CID or SID in PubChem'
    
    # 统一返回JSON字符串
    return json.dumps(result, ensure_ascii=False)

if __name__ == "__main__":
    name="Dimethyloxosilane"
    print(process_chemical(name))
    #file_path = "chemicals.xlsx"
