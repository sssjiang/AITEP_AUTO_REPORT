import utils.Pubmed as Pubmed
import json
# from utils.WebSearch import SearchWithCache
# searcher = SearchWithCache(cache_path="./cached")
from utils.perplexity_AI_search import PerplexityWithCache
from utils.llm_utils import AITEP
perplexity_api = PerplexityWithCache()
ai = AITEP()
def get_chemical_info(name):
    """
    获取化学物质的基本信息，优先使用PubMed，如果失败则使用网络搜索
    
    参数:
        name (str): 化学物质名称
        
    返回:
        str: 包含化学物质信息的JSON字符串
    """
    # 默认结果结构
    result = {
        "status": "success",
        "message": "",
        "drug_name": "None",
        "Synonyms": "None",
        "CAS Number": "None",
        "Molecular Formula": "None",
        "Molecular Weight": "None",
        "Smiles": "None",
        "InchI Key": "None",
        "reference_links": ["None"],
        "AI_search_results": "",
        "GAI_original": "",
        "IUPAC Name": "None",
        "Description": "None",
        "ATC Code": "None",
        "Pharmacotherapeutic Group": "None",
        "Appearance": "None",
        "Solubility": "None",
    }
    
    try:
        # 首先尝试使用PubMed获取信息
        json_data = Pubmed.process_chemical(name)
        pubmed_result = json.loads(json_data) if isinstance(json_data, str) else json_data
        
        # 如果PubMed返回错误，尝试使用网络搜索
        # if pubmed_result.get('status') == 'error':
        return _search_chemical_info(name, result)
        
        # 将PubMed结果合并到我们的结果结构中
        if isinstance(pubmed_result, dict):
            # 保留status和message字段
            result["status"] = pubmed_result.get("status", "success")
            result["message"] = pubmed_result.get("message", "")
            # 更新化学物质信息字段
            for key in result.keys():
                if key not in ["status", "message"] and key in pubmed_result:
                    result[key] = pubmed_result[key]
        
    except Exception as e:
        # 处理任何异常，尝试备用方法
        print(f"Error in PubMed process: {str(e)}")
        return _search_chemical_info(name, result)
    
    # 返回JSON字符串
    return json.dumps(result, ensure_ascii=False)

# AI搜索
def _search_chemical_info(name, default_result):
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
        search_prompt = f'search drug {name} basic information: Synonyms, CAS Number, Molecular Formula, Molecular Weight, Smiles, InchI Key, IUPAC Name, Description, ATC Code, Pharmacotherapeutic Group, Appearance, Solubility'
        
        # 执行搜索
        # json_data = searcher.search(search_prompt)
        json_data = perplexity_api.search(search_prompt)
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

                 Based on the search results in JSON format above, extract the basic  information for drug name (`drug_name`) with the following requirements:

                Input:
                - `drug_name`: {{DRUG_NAME}}

                Requirements:
                - Only analyze and extract info based on the content between **Content Start** and **Content End**
                - When the content between **Content Start** and **Content End** does not contain information about `drug_name`, directly output the following content and ignore subsequent instructions:
                ```json
                {
                    "drug_name": "None",
                    "Synonyms": ["None"],
                    "CAS Number": "None",
                    "Molecular Formula": "None",
                    "Molecular Weight": "None",
                    "Smiles": "None",
                    "InchI Key": "None",
                    "reference_links":["None"],
                    "IUPAC Name": "None",
                    "Description": "None",
                    "ATC Code": "None",
                    "Pharmacotherapeutic Group": "None",
                    "Appearance": "None",
                    "Solubility": "None",
                }
                ```
                """
            
            # 替换提示中的占位符
            formatted_prompt = prompt_template.replace("{{DRUG_NAME}}", name)
            formatted_prompt = formatted_prompt.replace("{{RESULTS}}", json.dumps(data_dict, ensure_ascii=False))
            
            # 调用AI处理
            ai_response = ai.run_llm(file_id=None, llm_model="qwen-plus", prompt=formatted_prompt)
            default_result["GAI_original"] = ai_response
          
            # 提取结果
            if isinstance(ai_response, dict):
                # 更新化学物质信息字段，保留status和message
                ai_response=ai_response.get("data")
                for key in ai_response:
                    if key in default_result and key not in ["status", "message"]:
                        default_result[key] = ai_response[key]
            elif isinstance(ai_response, str):
                try:
                    parsed_response = json.loads(ai_response)
                    # 更新化学物质信息字段，保留status和message
                    ai_response=ai_response.get("data")
                    for key in parsed_response:
                        if key in default_result and key not in ["status", "message"]:
                            default_result[key] = parsed_response[key]
                except:
                    default_result["status"] = "error"
                    default_result["message"] = f"Failed to parse AI response for {name}"
        else:
            default_result["message"] = f"{name}: No search results"
    
    except Exception as e:
        default_result["status"] = "error"
        default_result["message"] = f"Error in search process: {str(e)}"
    
    # 返回JSON字符串
    return json.dumps(default_result, ensure_ascii=False)

if __name__ == "__main__":
    print(get_chemical_info("Turpentine Oil"))
