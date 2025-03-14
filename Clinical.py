import requests
import json
import re
from bs4 import BeautifulSoup
from utils.search_utils import perform_search
import pandas as pd
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
# especial for daily_med need to upgrade
# 设置了当路径不可用时，值为空。 strict 模式
prompt ="""
# **Task: Deep Search and Extract the "drug info" for %s in %s route**

Focus on official product documentation and prescribing information. Prioritize information from:
1. Official drug package inserts and prescribing information
2. Regulatory authority documents (dailymed, FDA, EMA, NMPA, PMDA, EMC, DPD, drugs.com, MIMS etc.)
3. Summary of Product Characteristics (SPC)
4. Official drug monographs
5. Professional pharmaceutical databases
6. Other infomation source
Please output strictly according to the following JSON format, ensuring all content uses markdown format:

```json
{
    "ingredients": ["All active ingredients of this drug"],
    "route": "Administration route",
    "result": "### Clinical Therapeutic Doses\\n\\n| Species | Treatment | Route | Dosage |\\n|---------|-----------|--------|---------|\\n| ... | ... | ... | ... |\\n\\n<br>\\n\\n### Adverse Effects\\n\\n[Summary of side effects in one paragraph]\\n\\n<br>\\n\\n### Warning\\n\\n[Summary of medication warnings in one paragraph]\\n\\n<br>\\n\\n### Box warning\\n\\n**Black Box Warning:**\\n\\n[Summary of black box warning in one paragraph]\\n\\n<br>\\n\\n### Clinical Critical Effects\\n\\nThe critical or lead effects of [drug name] in clinical data were treatment of [disease].[reference_links]",
    "dosage_detail": {
        "frequency": "Number of applications per day (e.g., 'once daily', 'twice daily', or specific frequency)",
        "amount_per_use": "Quantity per application (e.g., 'thin film', '1-2 inches', specific weight)",
        "percentages":["Active ingredient concentration(e.g., '0.05%%', '0.1%%') / percentage_or_ratio( '60%%', '40%%')"]
        "formulations": ["Available formulations (cream, gel, ointment, etc.)"],
        "strength": "Potency information if available",
        "min_daily_dose": "minimum recommended daily dose if specified"
    }
}
```

Format requirements:
- JSON must fully comply with standards, with no extra line breaks or control characters
- If information about the drug in the specified route cannot be found, set "route", "result", and "dosage_detail" to null
- When information is available, content in the result field must strictly follow this structure:
    - Clinical Therapeutic Doses: Must be in markdown table format with four columns
    - Each section title must start with ###
    - Sections must be separated by <br>
    - Box warning content must start with "Black Box Warning:"
    - Clinical Critical Effects must use the specified sentence structure

Validation rules:
- drug_name cannot be empty
- result must include all five sections
- Clinical Therapeutic Doses must be a valid markdown table
- All sections must be arranged in the specified order
- HTML tags are not allowed (except <br>)
- No additional formatting marks are allowed

Error examples:
- Incorrect table format
- Missing section separator <br>
- Using other HTML tags
- Box warning not using correct marking
- Clinical Critical Effects not using specified sentence structure

"""
# markdown table format
def write_to_database(text):
    # 替换 \n\n 为两个空行，段落更清晰
    if text:
        text = text.replace("\\n\\n", "\n\n")
        # 替换 \n 为实际换行
        text = text.replace("\\n", "\n")
    return text


import pandas as pd
import json
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
from tqdm import tqdm


def clinical(ingredient, route):
    """
    处理单行数据的函数
    
    参数:
        ingredient (str): 成分名称
        route (str): 给药途径
        
    返回:
        str: 包含处理结果的JSON字符串
    """
    result = {
        "ingredient": "",
        "route": "",
        "new_generate_content": "",
        "dosage_detail": "",
        "new_citation": "",
        "status": "success",
        "message": ""
    }
    
    try:
        # 检查是否有有效值
        searchword = prompt % (ingredient, route)

        # 调用API获取搜索结果
        result_json = perform_search(searchword)
        # 确保result_json是有效的JSON字符串
        result_json = json.loads(result_json) if isinstance(result_json, str) else result_json
        # 解析搜索结果
        api_result = extract_json_data(result_json)
        
        # 提取内容
        content_json = extract_json_from_text(api_result.get("contents", ""))
        
        # 填充结果字段
        result["new_generate_content"] = write_to_database(content_json.get("result", ""))
        result["ingredient"] = content_json.get("ingredients", "")
        result["route"] = content_json.get("route", "")
        result["dosage_detail"] = content_json.get("dosage_detail", "")
        result["new_citation"] = api_result.get("citations", "")
        result["original_GAI"] = result_json
        
    except Exception as e:
        # 发生异常时记录错误信息
        result["status"] = "error"
        result["message"] = str(e)
    
    # 将结果转换为JSON字符串并返回
    return json.dumps(result, ensure_ascii=False)

if __name__ == "__main__":
    result=clinical("Abacavir", "Oral")
    print(type(result))
    print(result)

   
   
   

    
    