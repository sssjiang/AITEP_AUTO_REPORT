from openai import OpenAI
import os
import json
import pandas as pd
import re
from concurrent.futures import ThreadPoolExecutor
from utils.llm_utils import AITEP

prompt = """
# **Task: Evaluate Toxicity Nature and Assign Coefficient with Rationale**

As a toxicology assessment expert, analyze the provided content to evaluate the nature of toxicity across all categories, determine the highest coefficient value (`F4_value`), and provide a clear and concise rationale (`Rationale`) based on established criteria.

---

### **Content**  
**Input:**  
{{CONTENT}}  
**End**


### **Step 1: Calculate Values for All three Categories**  
Evaluate each category independently and assign its respective value based on the criteria below:

#### **1. Reproductive Studies(include Reproductive animal) Value**  
- Fetal toxicity **with maternal toxicity**: `1`  
- Fetal toxicity **without maternal toxicity**: `5`  
- Teratogenic effect **with maternal toxicity**: `5`  
- Teratogenic effect **without maternal toxicity**: `10`  

#### **2. Animal Toxicology Studies Value**  
Check for the presence of **any** of the following toxicities:  
- Carcinogenicity  
- Genotoxicity  
- Neurotoxicity  
- Teratogenicity
- Highly Sensitizing Potential 

Values:  
- If **one or more** of the above toxicities are present: `10`  
- If **none** of the above toxicities are present: `1`  

#### **3. Clinical Studies Value**  
- Black box warning present: `5`  
- No severe toxicity at the lowest clinical dose: `1`  

---

### **Step 2: Determine Final Value**  
- Calculate the values for all three categories.  
- Identify the **highest value** among the three categories and assign it as the final `F4_value`.  
- Document the category (or categories) that contributed to the final value.  

---

### **Output Requirements**  
Provide the results in JSON format, including:  
- `reproductive_value`: The value calculated for reproductive studies.  
- `animal_tox_value`: The value calculated for animal toxicology studies.  
- `clinical_value`: The value calculated for clinical studies.  
- `F4_value`: The final coefficient value, which is the highest among all categories.  
- `Rationale`: A clear explanation of the values assigned to each category and the rationale for selecting the final `F4_value`.  
- For any category with insufficient information, use `"No Data"`.
- No explaination
---

#### **Example Output**  
```json
{
    "reproductive_value": 1,
    "animal_tox_value": 10,
    "clinical_value": 1,
    "F4_value": 10,
    "Rationale": "Reproductive studies showed fetal toxicity with maternal toxicity (1). Animal toxicology studies indicated the presence of neurotoxicity at PoD (10). Clinical studies showed no severe toxicity at the lowest clinical dose (1). The highest value, 10, was selected from animal toxicology studies."
}
```
"""




# 定义处理单行数据的函数

def F4_value(clinical, hazards):
    """
    计算F4因子值
    
    参数:
        clinical (str): 临床数据
        hazards (str或list): 危害识别数据的JSON字符串或列表
        
    返回:
        str: 包含F4因子计算结果的JSON字符串
    """
    result = {
        "factors": "F4",
        "value": None,
        "rationale": "",
        "status": "success",
        "GAI_original": "",
        "message": ""
    }
    
    try:
        # 解析危害识别数据
        hazards_data = hazards
        if isinstance(hazards, str):
            hazards_data = json.loads(hazards)
        
        # 创建生殖毒性数据结构和其他毒性数据列表
        reproductive_data = None
        hazard_list = []

        # 遍历所有危害数据，根据param1进行分类处理
        for hazard in hazards_data:
            hazard_type = hazard['param1']
            toxicity_value = hazard['param2']
            detail_info = hazard['param3']
            
            hazard_info = {
                "toxicity_value": f"{hazard_type} has toxicity? {toxicity_value}",
                "detail_info": detail_info
            }
            
            # 如果是生殖毒性，单独处理
            if hazard_type == "Reproductive/Developmental Toxicant":
                reproductive_data = hazard_info
            else:
                # 其他类型的毒性添加到列表中
                hazard_list.append(hazard_info)

        # 如果没有找到生殖毒性数据，创建一个空的默认值
        if reproductive_data is None:
            reproductive_data = {
                "toxicity_value": "Reproductive/Developmental Toxicant has toxicity? Unknown",
                "detail_info": "No data available"
            }
        
        # 创建最终的JSON内容
        json_content = {
            "reproductive_data": reproductive_data,
            "animal_tox_data": hazard_list,
            "clinical_data": clinical
        }
        
        # 调用AI模型计算F4值
        ai = AITEP()

        formatted_prompt = prompt.replace("{{CONTENT}}", json.dumps(json_content, ensure_ascii=False))      
        response = ai.run_llm(file_id=None, llm_model="qwen-plus", prompt=formatted_prompt)
        result["GAI_original"] = response
        # 解析AI响应获取F4值和理由
        try:
            parsed_response = json.loads(response) if isinstance(response, str) else response
            result["value"] = parsed_response.get("data").get("F4_value", None)
            result["rationale"] = parsed_response.get("data").get("Rationale", "")
        except:
            result["message"] = "Failed to parse AI response"

        
    except Exception as e:
        result["status"] = "error"
        result["message"] = str(e)
    
    # 将结果转换为JSON字符串并返回
    return json.dumps(result, ensure_ascii=False)

if __name__ == "__main__":
    clinical="### Clinical Therapeutic Doses\n\n| Species | Treatment | Route | Dosage |\n|---------|-----------|--------|---------|\n| Adults | HIV-1 infection | Oral | 600 mg once daily or 300 mg twice daily |\n| Pediatric patients (≥14 kg) | HIV-1 infection | Oral | Dose calculated based on body weight, not exceeding 600 mg daily |\n\n<br>\n\n### Adverse Effects\n\nAbacavir can cause serious hypersensitivity reactions, lactic acidosis, severe hepatomegaly with steatosis, and immune reconstitution syndrome. Common side effects include nausea, vomiting, fever, and fatigue.\n\n<br>\n\n### Warning\n\nAbacavir should be used with caution in patients with a history of cardiovascular disease due to an increased risk of myocardial infarction. It is also important to monitor for signs of lactic acidosis and severe hepatomegaly with steatosis.\n\n<br>\n\n### Box warning\n\n**Black Box Warning:**\n\nSerious and sometimes fatal hypersensitivity reactions have occurred with abacavir. Patients who carry the HLA-B*5701 allele are at a higher risk of these reactions. Abacavir is contraindicated in patients with a prior hypersensitivity reaction to abacavir or in those with the HLA-B*5701 allele.\n\n<br>\n\n### Clinical Critical Effects\n\nThe critical or lead effects of abacavir in clinical data were the treatment of HIV-1 infection[1][3]."
    hazard=[{'param1': 'Genotoxicant', 'param2': 'Yes', 'param3': 'The genotoxic potential of abacavir is supported by multiple studies, including those from peer-reviewed scientific literature. While regulatory authorities have not explicitly classified it as a genotoxicant, the evidence from animal and in vitro studies suggests that abacavir can induce genetic damage, particularly in combination with other drugs.'}, {'param1': 'Carcinogen', 'param2': 'Unknown', 'param3': "While abacavir has shown carcinogenic effects in animal studies, it is not classified as a carcinogen by major regulatory bodies. The evidence from animal studies suggests potential carcinogenic activity, but this is not sufficient for a definitive classification as a human carcinogen. Therefore, the result is 'Unknown' due to conflicting evidence and lack of human epidemiological data."}, {'param1': 'Reproductive/Developmental Toxicant', 'param2': 'No', 'param3': 'While animal studies suggest potential developmental toxicity, extensive human data from pregnancy registries do not indicate an increased risk of major birth defects. Therefore, the risk in humans is considered low based on available evidence.'}, {'param1': 'Highly Sensitizing Potential', 'param2': 'Yes', 'param3': 'The FDA and other regulatory bodies have issued warnings about the hypersensitivity potential of abacavir, particularly in individuals with the HLA-B*5701 allele. Peer-reviewed literature consistently supports the high sensitizing potential of abacavir, making it a well-documented risk.'}]
    print(F4_value(clinical, hazard))