from utils.perplexity_AI_search import PerplexityWithCache
import json
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import json
# especial for daily_med need to upgrade
def extract_json_from_text(text):
        """
        从文本中提取并解析JSON对象
        
        参数:
            text (str): 包含JSON对象的文本
        
        返回:
            dict: 解析后的JSON对象，如果解析失败返回None
        """
        dict_pattern = r'```json\s*([\s\S]*?)\s*```'
        match = re.search(dict_pattern, text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError as e:
                print("match",match)
                print("JSON解析失败:", e)
                return None
        else:
            print("未找到 ```json 和 ``` 标记中的 JSON 对象。")
            return None
def extract_json_data(data):
    try:
        # 解析JSON字符串
        data = json.loads(data)
        
        # 提取所需信息
        model = data.get("model", "")
        citations = data.get("citations", [])
        # 提取所有content
        contents = []
        if "choices" in data:
            for choice in data["choices"]:
                if "message" in choice and "content" in choice["message"]:
                    contents.append(choice["message"]["content"])
        contents_string = "".join(contents)
        # 返回提取的信息

        return {
            "model": model,
            "citations": citations,
            "contents": contents_string
        }
    
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format"}
    except Exception as e:
        return {"error": str(e)}

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

import json

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
        perplexity_api = PerplexityWithCache()
        result_json = perplexity_api.search(searchword)

        result["GAI_original"] = result_json
        # 解析搜索结果
        api_result = extract_json_data(result_json)
        result["citation"] = api_result.get("citations", "")
        # 提取内容
        content_json = extract_json_from_text(api_result.get("contents", ""))
        
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
    ingredient = "Abacavir"
    result = all_toxicities(ingredient)
    print(type(result))
    print(result)

    



    