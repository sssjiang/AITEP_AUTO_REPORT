import utils.PubChem as PubChem
import json
from utils.llm_utils import AITEP
from utils.search_utils import perform_search
ai = AITEP()
def get_chemical_info(name,search_method="perplexity"):
    """
    获取化学物质的基本信息，优先使用PubMed，如果失败则使用网络搜索
    
    参数:
        name (str): 化学物质名称
        
    返回:
        str: 包含化学物质信息的JSON字符串
    """
    # 默认结果结构
    default_result = {
        "status": "success",
        "message": "",
        "drug_name": "",
        "Synonyms": "",
        "CAS Number": "",
        "Molecular Formula": "",
        "Molecular Weight": "",
        "Smiles": "",
        "InchI Key": "",
        "reference_links": "",  
        "AI_search_results": "",
        "GAI_original": "",
        "IUPAC Name":"",
        "Description": "",
        "ATC Code": "",
        "Pharmacotherapeutic Group": "",
        "Appearance": "",
        "Solubility": "",
    }
    
    try:
        # 首先尝试使用PubMed获取信息
        json_data = PubChem.process_chemical(name)
        pubmed_result = json.loads(json_data) if isinstance(json_data, str) else json_data
        
        # 将PubMed结果合并到我们的结果结构中
        if pubmed_result.get("status") == "success":
            # 更新化学物质信息字段
            for key in pubmed_result.keys():
                if key not in ["status", "message"] and key in pubmed_result:
                    default_result[key] = pubmed_result[key]
    
         # 检查是否有空缺的值("")
        has_missing_values = False
        for key, value in default_result.items():
            if key not in ["status", "message", "AI_search_results", "GAI_original"] and value == "":
                has_missing_values = True
                break
        # 如果有空缺的值，使用搜索补充
        if has_missing_values:
            search_result=_search_chemical_info(name,search_method, default_result)
            if search_result.get("status") == "success":
                default_result = search_result
    except Exception as e:
        # 处理任何异常，尝试备用方法
        print(f"Error in PubMed process: {str(e)}")
        default_result["status"] = "error"
        default_result["message"] = f"Error in PubMed process: {str(e)}"
    # 返回JSON字符串
    return json.dumps(default_result, ensure_ascii=False)

# AI搜索
def _search_chemical_info(name,search_method, default_result):
    """
    使用网络搜索获取化学物质信息的辅助函数
    
    参数:
        name (str): 化学物质名称
        default_result (dict): 默认返回结果
        
    返回:
        str: 包含化学物质信息的JSON字符串
    """
    try:
        # 构建搜索提示
        search_prompt = f"""
        search comprehensive drug profile for {name} including official identifiers (CAS, SMILES, InChI Key), chemical properties (formula, molecular weight, IUPAC name), pharmaceutical characteristics (appearance, solubility), and clinical information (ATC code, therapeutic group, indications, pharmacokinetics).
        """
        
        # 执行搜索

        json_data = perform_search(search_prompt, search_method)
        data_dict = json.loads(json_data) if isinstance(json_data, str) else json_data
        default_result["AI_search_results"] = data_dict
        # 如果搜索有结果，使用AI处理
        if data_dict and len(data_dict) > 0:
            # 构建AI提示
            prompt_template = """
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
            
            # 替换提示中的占位符
            formatted_prompt = prompt_template.replace("{{DRUG_NAME}}", name)
            formatted_prompt = formatted_prompt.replace("{{RESULTS}}", json.dumps(data_dict, ensure_ascii=False))
            
            # 调用AI处理
            ai_response = ai.run_llm(file_id=None, llm_model="qwen-plus", prompt=formatted_prompt)
            default_result["GAI_original"] = ai_response
 
            # 更新空缺的值
            ai_response=ai_response.get("data")
            for key in ai_response.keys():
                if key not in ["status", "message"] and key in default_result and default_result[key] == "":
                    default_result[key] = ai_response[key]
        else:
            default_result["message"] = f"{name}: No search results"
    
    except Exception as e:
        default_result["status"] = "error"
        default_result["message"] = f"Error in search process: {str(e)}"
    
    # 返回JSON字符串
    return default_result

if __name__ == "__main__":
    print(get_chemical_info("Turpentine Oil"))
