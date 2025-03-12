from utils.llm_utils import AITEP
import json
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import pandas as pd
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import threading
# especial for daily_med need to upgrade

loose_prompt="""
   Content Start
    ```json
    {{CONTENT}}
    ```
    Content End
base on the JSON content above,
Calculate the minimum daily therapeutic dose for this ingredient %s in adults (Point of Departure, PoD), converting to mg/day.

Please provide your response ONLY in the following JSON format without any additional text:
```json
{
    "PoD": <numeric_value_only_or_null>,
    "PoD_unit": <"mg/day"_or_null>,
    "PoD_calculate_detail": "<detailed calculation process or explanation why calculation is not possible>",
    "assumptions_made": ["List of assumptions used in calculation"]
}
Instructions:

    - For PoD, include ONLY the numeric value without units
    - Convert all units to mg/day when possible
    - In PoD_calculate_detail, show all calculation steps including unit conversions
    - Document all assumptions made during calculations
    - If multiple dosage forms exist, use the lowest effective dose
    - For time-dependent dosing, use the minimum daily maintenance dose
    - Ensure the response is valid JSON that can be parsed programmatically

Standard assumptions allowed when specific information is missing:
1.Droppers/Drops:
    - Standard drop volume: 0.05 mL/drop
    - Standard dropper size: 1 mL
    - Minimum drops per application: 1 drop
2.Topical applications:
    - Standard application amount: 2 mg/cm² or thin film
    - Default application frequency: twice daily if not specified
    - Standard application length for lines/strips: 2.5 cm
    - Standard area for "thin film": 10 cm²
3.Oral solutions/suspensions:
    - Standard teaspoon: 5 mL
    - Standard tablespoon: 15 mL
4.Spray applications:
    - Standard spray volume: 0.1 mL/spray
    - Minimum sprays per application: 1 spray
Set "PoD" and "PoD_unit" to null ONLY if:
    - No dosage information is available even after applying standard assumptions
    - The drug is explicitly contraindicated for the specified route
    - The calculation would require non-standard assumptions beyond those listed above
"""
# 是否有必要在这里data_out
def PoD_value(ingredient, **kwargs):
    """
    处理单行数据的函数，将成分和其他参数传入LLM进行处理
    
    参数:
        ingredient (str): 成分名称
        **kwargs: 关键字参数，这些参数将被格式化为内容字符串
        
    返回:
        str: 包含处理结果的JSON字符串
    """
    result = {
        "params": kwargs,  # 记录传入的关键字参数
        "status": "success",
        "message": "",
        "GAI_origin": "",
        "PoD_value": None,
        "PoD_unit": "",
        "point_of_departure": "",
        "point_of_departure_detail": "",
    }
    
    try:
        # 构建内容字符串，将所有关键字参数格式化为"参数名=参数值"的形式
        param_strings = [f"{key}={value}" for key, value in kwargs.items()]
        
        # 将参数字符串连接成一个内容字符串
        content = ", ".join(param_strings)
        
        # 构建提示词
        prompt = loose_prompt % (ingredient)
        newPrompt = prompt.replace("{{CONTENT}}", content)
        
        # 调用AI模型
        ai = AITEP()
        llm_result = ai.run_llm(file_id=None, llm_model="qwen-plus", prompt=newPrompt)
        # 保存处理结果
        result["GAI_origin"] = llm_result
        pods=llm_result.get("data")
        pod = pods.get("PoD", None)
        pod_unit = pods['PoD_unit']
        point_of_departure = str(pod) + " " + pod_unit
        point_of_detail = pods["PoD_calculate_detail"]
        result["PoD_value"] = pod
        result["PoD_unit"] = pod_unit
        result["point_of_departure"] = point_of_departure
        result["point_of_departure_detail"] = point_of_detail
        
    except Exception as e:
        # 异常处理
        result["status"] = "error"
        result["message"] = str(e)
        print(f"Error processing ingredient '{ingredient}' with params {kwargs}: {str(e)}")
    
    # 将结果转换为JSON字符串并返回
    return json.dumps(result, indent=4, ensure_ascii=False)



if __name__ == "__main__":
    # main()
    clinical="### Clinical Therapeutic Doses\n\n| Species | Treatment | Route | Dosage |\n|---------|-----------|--------|---------|\n| Adults | HIV-1 infection | Oral | 600 mg once daily or 300 mg twice daily |\n| Pediatric patients (≥14 kg) | HIV-1 infection | Oral | Dose calculated based on body weight, not exceeding 600 mg daily |\n\n<br>\n\n### Adverse Effects\n\nAbacavir can cause serious hypersensitivity reactions, lactic acidosis, severe hepatomegaly with steatosis, and immune reconstitution syndrome. Common side effects include nausea, vomiting, fever, and fatigue.\n\n<br>\n\n### Warning\n\nAbacavir should be used with caution in patients with a history of cardiovascular disease due to an increased risk of myocardial infarction. It is also important to monitor for signs of lactic acidosis and severe hepatomegaly with steatosis.\n\n<br>\n\n### Box warning\n\n**Black Box Warning:**\n\nSerious and sometimes fatal hypersensitivity reactions have occurred with abacavir. Patients who carry the HLA-B*5701 allele are at a higher risk of these reactions. Abacavir is contraindicated in patients with a prior hypersensitivity reaction to abacavir or in those with the HLA-B*5701 allele.\n\n<br>\n\n### Clinical Critical Effects\n\nThe critical or lead effects of abacavir in clinical data were the treatment of HIV-1 infection[1][3]."
    dosage_detail={"frequency": "twice daily", "amount_per_use": "300 mg", "percentages": ["100%"], "formulations": ["Tablet"], "strength": "300 mg", "min_daily_dose": "300 mg"}
    # 可以接受dict
    json_result=PoD_value("Abacavir",clinical=clinical,dosage_detail=dosage_detail)

    



    