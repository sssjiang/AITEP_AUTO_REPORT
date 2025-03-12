from openai import OpenAI
import os
import json
import pandas as pd
import re
from concurrent.futures import ThreadPoolExecutor
from utils.llm_utils import AITEP
prompt = """
# **Task: Evaluate LOAEL/NOAEL Status and Assign Coefficient with Rationale**

As a toxicology assessment expert, analyze the provided content to determine the LOAEL/NOAEL status, assign the appropriate coefficient value (`F5_value`), and provide a clear and concise rationale (`Rationale`) based on established criteria.

---

### **Content**  
**Start:**  
{{CONTENT}}  
**End**

---

### **Step 1: Assign Coefficient Value Based on Study Type**  
- **NOAEL (No adverse effects):** Assign `F5_value = 1`.  
- **LOAEL (Adverse effects observed):** Assign `F5_value` within the range `2-5` (based on severity).

---

### **Step 2: Finalize the Coefficient Value**  
- Apply the appropriate value range from Step 1.  
- For LOAEL cases, select a specific value within the range based on the severity of observed effects.

---

### **Output Requirements**  
Provide the results in JSON format, including:  
- `Effect_Level`: The observed effect level (e.g., NOAEL, LOAEL).  
- `F5_value`: The final assigned coefficient value.  
- `Rationale`: A clear explanation of the classification and value selection.  
- If insufficient information is available, return `"No Data"`.

---

#### **Example Output**  
```json
{
    "Effect_Level": "LOAEL",
    "F5_value": 4,
    "Rationale": "The study was classified as an animal toxicology study. LOAEL was identified without NOAEL establishment. A value of 4 was assigned within the LOAEL range (3-5) based on the severity of observed effects."
}
```

"""
def F5_value(PoD_detail, clinical_data):
    result = {
        "factors": "F5",  # 假设这是处理PoD相关的数据
        "value": None,
        "rationale": "",
        "status": "success",
        "GAI_original": "",
        "message": ""
    }
    
    try:
        
        # 创建JSON内容
        json_content = {
            "clinical_data": clinical_data,
            "PoD_detail": PoD_detail
        }
        
        # 调用AI模型获取响应
        ai = AITEP()
        formatted_prompt = prompt.replace("{{CONTENT}}", json.dumps(json_content, ensure_ascii=False))
        response = ai.run_llm(file_id=None, llm_model="qwen-plus", prompt=formatted_prompt)
        result["GAI_original"] = response
        
        # 解析AI响应
        try:
            parsed_response = json.loads(response) if isinstance(response, str) else response
            result["value"] = parsed_response.get("data", {}).get("F5_value", None)
            result["rationale"] = parsed_response.get("data", {}).get("Rationale", "")
        except:
            result["message"] = "Failed to parse AI response"
            
    except Exception as e:
        result["status"] = "error"
        result["message"] = str(e)
    
    # 返回索引和结果的JSON字符串
    return json.dumps(result, ensure_ascii=False)


if __name__ == '__main__':
    PoD_detail="{'PoD_value': 0.5, 'PoD_unit': 'mg/kg/day', 'point_of_departure': '0.5 mg/kg/day', 'point_of_departure_detail': 'The PoD was determined based on the NOAEL of 50 mg/kg/day from a 90-day oral toxicity study in rats, applying an uncertainty factor of 100.'}"
    clinical="### Clinical Therapeutic Doses\n\n| Species | Treatment | Route | Dosage |\n|---------|-----------|--------|---------|\n| Adults | HIV-1 infection | Oral | 600 mg once daily or 300 mg twice daily |\n| Pediatric patients (≥14 kg) | HIV-1 infection | Oral | Dose calculated based on body weight, not exceeding 600 mg daily |\n\n<br>\n\n### Adverse Effects\n\nAbacavir can cause serious hypersensitivity reactions, lactic acidosis, severe hepatomegaly with steatosis, and immune reconstitution syndrome. Common side effects include nausea, vomiting, fever, and fatigue.\n\n<br>\n\n### Warning\n\nAbacavir should be used with caution in patients with a history of cardiovascular disease due to an increased risk of myocardial infarction. It is also important to monitor for signs of lactic acidosis and severe hepatomegaly with steatosis.\n\n<br>\n\n### Box warning\n\n**Black Box Warning:**\n\nSerious and sometimes fatal hypersensitivity reactions have occurred with abacavir. Patients who carry the HLA-B*5701 allele are at a higher risk of these reactions. Abacavir is contraindicated in patients with a prior hypersensitivity reaction to abacavir or in those with the HLA-B*5701 allele.\n\n<br>\n\n### Clinical Critical Effects\n\nThe critical or lead effects of abacavir in clinical data were the treatment of HIV-1 infection[1][3]."
    print(F5_value(PoD_detail, clinical))

    


