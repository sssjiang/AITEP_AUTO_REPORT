import json
from utils.search_utils import perform_search
from utils.search_utils import PerplexitySearch
import json
# especial for daily_med need to upgrade


regulation_prompt="""
# Task: Deep Search and Extract the "%s" toxicity information for the drug active ingredient: %s

Please output strictly according to the following JSON format:

```json
{
    "ingredient_name": "Abacavir",
    "section_name": "%s",
    "content": "Extracted content about the ingredient's %s.",
    "link": ["reference_links_to_the_extracted_content"],
    "result": "Yes/No/Unknown",
    "result_detail": "Detailed explanation of the %s conclusion and source conflicts if any"
}
Guidelines:
1. Source Hierarchy and Result Determination:
Priority order for information sources:
    1.1 Regulatory authorities (FDA, EMA, WHO ECHA etc.)
    1.2 Official pharmacopeias
    1.3 Peer-reviewed scientific literature (PubMed, sciencedirect etc.)
    1.4 Other validated sources
    1.5 other sources

2. Result Classification Rules:
When sources from different levels conflict:
    If higher-level source indicates "Yes" and lower-level source indicates "No" → Result = "Yes"
    If higher-level source indicates "No" and lower-level source indicates "Yes" → Result = "No"
When sources from the same level conflict:
    If any sources within the same level show conflicting results (Yes/No) → Result = "Unknown"
"Unknown" cases also include:
    Insufficient evidence
    No data available

3. **Ensure Valid JSON**:
   - The final output must be a correctly formatted JSON object with proper syntax.
   - All fields (`ingredient_name`, `section_name`, `content`, and `link` and `result` and `result_detail`) must be included.

4. **Focus on Accuracy**:
   - Review the content thoroughly to ensure accurate extraction of the required information.

5. **Professional Summary**:
   - Ensure the summary of the content is clear, professional, and concise.

"""


def process_toxicity(ingredient, toxicity_type="Genotoxicity"):
    """
    处理单个成分的毒性信息
    
    参数:
        ingredient (str): 成分名称
        toxicity_type (str): 毒性类型，默认为"Genotoxicity"
        
    返回:
        str: 包含处理结果的JSON字符串
    """
    result = {
        "toxicity_type": toxicity_type,
        "reference_links": "",
        "result": "",
        "result_detail": "",
        "citation": "",
        "content": "",
        "section_name": "",
        "ingredient_name":"",
        "status":"success",
        "message":"",
        "GAI_original": ""
    }
    
    try:
        # 构建搜索查询
        searchword = regulation_prompt % (toxicity_type, ingredient, toxicity_type, toxicity_type, toxicity_type)
        
        # 调用API获取搜索结果
        result_json = perform_search(searchword)
        # 确保result_json是有效的JSON字符串
        result_json = json.loads(result_json) if isinstance(result_json, str) else result_json
        result["GAI_original"] = result_json
        # 解析搜索结果 (后处理方法)
        api_result = PerplexitySearch.extract_json_data(result_json)

        result["citation"] = api_result.get("citations", "")
        # 提取内容 (后处理方法)
        content_json = PerplexitySearch.extract_json_from_content(api_result.get("contents", ""))
        
        # 填充结果字段
        result["ingredient_name"] = content_json.get("ingredient_name","")
        result["section_name"] = content_json.get("section_name", "")
        result["content"] = content_json.get("content", "")
        result["reference_links"] = content_json.get("link", "")
        result["result"] = content_json.get("result", "")
        result["result_detail"] = content_json.get("result_detail", "")
    except Exception as e:
        # 发生异常时记录错误信息
        result["status"] = "error"
        result["message"] = str(e)
    
    # 将结果转换为JSON字符串并返回
    return json.dumps(result, ensure_ascii=False)

def all_toxicities(ingredient):
    """
    处理单个成分的多种毒性信息
    
    参数:
        ingredient (str): 成分名称
        
    返回:
        str: 包含所有毒性处理结果的JSON字符串
    """
    # 定义需要处理的毒性类型
    toxicity_types = [
        "Genotoxicant",
        "Carcinogen",
        "Reproductive/Developmental Toxicant",
        "Highly Sensitizing Potential"
    ]
    
    try:
        # 处理每种毒性类型
        toxicity_results = []
        for toxicity_type in toxicity_types:
            # 获取单个毒性的JSON结果并解析为Python对象
            toxicity_result_json = process_toxicity(ingredient, toxicity_type)
            toxicity_result = json.loads(toxicity_result_json)
            toxicity_results.append(toxicity_result)
        
        # 构建完整结果
        result = {
            "harzard_identification": toxicity_results,
            "status": "success",
            "message": ""
        }

    except Exception as e:
        # 发生异常时记录错误信息
        result = {
            "harzard_identification": [],
            "status": "error",
            "message": str(e)
        }
    
    # 将结果转换为JSON字符串并返回
    return json.dumps(result, ensure_ascii=False)

    
if __name__ == "__main__":
    # 测试
    ingredient = "Kaolin"
    result = all_toxicities(ingredient)
    print(type(result))
    print(result)

    



    