
import utils.Pubmed as Pubmed
import json
# from utils.WebSearch import SearchWithCache
from utils.perplexity_AI_search import PerplexityWithCache

# searcher = SearchWithCache(cache_path="./cached")
perplexity_api = PerplexityWithCache()
from utils.llm_utils import AITEP
ai = AITEP()
def get_pharmacokinetics(name):
    """
    获取药物的药代动力学和其他基本信息
    
    参数:
        name (str): 药物名称
        
    返回:
        dict: 包含药物信息的字典，或在失败时返回带有错误信息的字典
    """
    # 默认返回结果结构
    default_result = {
        "status": "success",
        "message": "",
        "Pharmacokinetics": {
            "Absorption": "",
            "Distribution": "",
            "Metabolism": "",
            "Excretion": ""
        },
        "Indication": "",
        "Pharmacodynamics": "",
        "Mechanism of Action": "",
        "reference_links": "",
        "AI_search_results": "",
        "GAI_original": ""
    }
    
    try:
        # 定义需要搜索的关键词
        base_info_keywords = [
            "Pharmacokinetics['Absorption','Distribution','Metabolism','Excretion']", 
            "Indication", 
            "Pharmacodynamics", 
            "Mechanism of Action"
        ]
        
        # 收集所有搜索结果
        contents = []
        for keyword in base_info_keywords:
            try:
                search_prompt = f'search the drug {name} for {keyword} information'
                # json_data = searcher.search(search_prompt)
                json_data = perplexity_api.search(search_prompt)
                # 确保json_data是有效的JSON字符串
                if not json_data:
                    print(f"Empty search result for {search_prompt}")
                    continue
                data_dict = json.loads(json_data) if isinstance(json_data, str) else json_data
                if data_dict:
                    contents.append({"keyword": keyword, "data": data_dict})
                else:
                    print(f"Empty parsed data for {search_prompt}")
            except Exception as e:
                print(f"Error searching for {keyword}: {str(e)}")
                # 继续处理下一个关键词，而不是整个函数失败
        default_result["AI_search_results"] = contents
        # 只有在有搜索结果时才调用AI处理
        if contents:
            # 构建AI提示
            prompt_template = """
Content Start
```json
{{RESULTS}}
```
Content End

Based on the search results in JSON format above, extract the basic information for drug name (`drug_name`) with the following requirements:

Input:
- `drug_name`: {{DRUG_NAME}}

Requirements:
- Only analyze and extract info based on the content between **Content Start** and **Content End**
- When the content between **Content Start** and **Content End** does not contain information about `drug_name`, directly output the following content and ignore subsequent instructions:
```json
{
    "drug_name": "Ibuprofen",
    "Pharmacokinetics": {
        "Absorption": "Rapidly absorbed from the gastrointestinal tract with peak plasma concentrations occurring within 2 hours",
        "Distribution": "Distributed throughout most body tissues with a volume of distribution of approximately 0.9 L/kg",
        "Metabolism": "Primarily metabolized in the liver via glucuronidation and sulfation pathways",
        "Excretion": "Excreted in urine as metabolites with an elimination half-life of 2-3 hours"
    },
    "Indication": "Treatment of mild to moderate pain and fever",
    "Pharmacodynamics": "Produces analgesia by inhibition of prostaglandin synthesis in the central nervous system and peripherally blocks pain impulse generation",
    "Mechanism of Action": "Selective inhibitor of cyclooxygenase (COX) enzymes with predominant effects on COX-2", 
    "reference_links": ["https://pubchem.ncbi.nlm.nih.gov/compound/Ibuprofen", "https://www.drugbank.ca/drugs/DB01050"]
}
```
                """
            
            # 替换提示中的占位符
            formatted_prompt = prompt_template.replace("{{DRUG_NAME}}", name)
            formatted_prompt = formatted_prompt.replace("{{RESULTS}}", json.dumps(contents, ensure_ascii=False))
            
            # 调用AI处理
            ai_response = ai.run_llm(file_id=None, llm_model="qwen-plus", prompt=formatted_prompt)
            default_result["GAI_original"] = ai_response
            # 处理AI响应
            # 确保返回的数据包含所需字段
            result = ai_response.get('data', {})
            for key in result:
                default_result[key] = result[key]
        else:
            default_result["status"] = "error"
            default_result["message"] = f"No search results found for {name}"
    
    except Exception as e:
        default_result["status"] = "error"
        default_result["message"] = f"Error in pharmacokinetics process: {str(e)}"
    
    return json.dumps(default_result, ensure_ascii=False)

        
if __name__ == "__main__":
    print(get_pharmacokinetics("Turpentine Oil"))
