from openai import OpenAI
import os
import json
import pandas as pd
import re
from utils.llm_utils import AITEP

prompt ="""
# **Task: Classify Study and Assign Coefficient with Rationale**

As a professional evaluation assistant, analyze the content provided below to assign the appropriate coefficient value (`F3_value`) based on the hierarchical rules outlined.

---

### **Content**  
**Start:**  
{{CONTENT}}  
**End**

### **Step1: Determine Coefficient Value Using Hierarchical Rules**
Apply the following rules in order of priority to assign the coefficient value (`F3_value`):

#### **Priority 1: Explicit Duration**
- Duration < 2 weeks: `10`
- Duration = 2 weeks: `5`
- Duration > 2 weeks: `1`

#### **Priority 2: Duration Description**
If explicit duration is not available, check for:
- "chronic treatment," "long-term administration": `1`
- "acute treatment," "short-term study": `10`
- "a few weeks," "intermediate duration": `5`

#### **Priority 3: Treatment Type**
If neither explicit duration nor duration description is available, classify by treatment:

**Long-term Use (Score 1)**
- Chronic Disease Management: hypertension, diabetes, hyperlipidemia, asthma
- Psychiatric Disorders: depression, anxiety, schizophrenia
- Autoimmune Diseases: rheumatoid arthritis, systemic lupus erythematosus
- Neurological Disorders: Parkinson's disease, epilepsy
- Endocrine Disorders: hyperthyroidism/hypothyroidism
- Osteoporosis prevention and treatment
- Post-organ transplant immunosuppression
- Chronic pain management

**Medium-term Use (Score 5)**
- Subacute Infections: certain bacterial infections requiring 2-4 weeks treatment
- Short-term treatment of moderate depression or anxiety
- Skin Conditions: moderate eczema, periodic treatment of psoriasis
- Digestive System Diseases: periodic treatment of gastric ulcer, colitis
- Post-surgical recovery medication

**Short-term Use (Score 10)**
- Acute Infections: common cold, flu, acute bronchitis
- Acute Pain: headache, toothache, muscle pain
- Allergic Reactions: urticaria, acute allergies
- Acute Inflammation: tonsillitis, otitis media
- Short-term insomnia
- Acute Gastrointestinal Symptoms: diarrhea, constipation
- Fever
- Minor Injuries: sprains, abrasions
- Perioperative short-term medication
- Acute respiratory infections

---

#### **Example Output**
```json
{
    "value": 5,
    "rationale": "The study is a clinical study with a duration of 2 weeks, categorized as sub-chronic."
}
```

---

### **Additional Notes**
- Ensure the rationale is concise and directly references the rules applied.  
- For ambiguous or insufficient information, clearly state the reason in the rationale (e.g., "Duration not provided" or "Study type unclear").  
- Focus on clarity and precision in both the classification and explanation.
- No explaination
---
"""
import json

def F3_value(content):
    """
    计算F3因子值
    
    参数:
        content (str): 用于计算F3因子的内容文本
        
    返回:
        str: 包含F3因子计算结果的JSON字符串
    """
    result = {
        "factors": "F3",
        "value": None,
        "rationale": "",
        "GAI_original": "",
        "status": "success",
        "message": ""
    }
    
    try:
        # 构建提示词
        formatted_prompt = prompt.replace('{{CONTENT}}', content)
        
        # 调用AI模型
        ai = AITEP()
        llm_result = ai.run_llm(file_id=None, llm_model="qwen-plus", prompt=formatted_prompt)
        
        # 存储原始响应
        result["GAI_original"] = llm_result
        
        # 这里可以添加对llm_result的解析逻辑，提取F3值和理由
        # 例如：可以从llm_result中解析出具体的F3值和理由
        # 如果llm_result已经是结构化数据，可以直接提取
        
        # 假设llm_result包含需要的信息，或需要进一步解析
        try:
            # 尝试解析结果，这里需要根据实际的llm_result格式调整
            parsed_result = json.loads(llm_result) if isinstance(llm_result, str) else llm_result
            
            # 提取值和理由
            if isinstance(parsed_result, dict):
                result["value"] = parsed_result.get("data").get("value", None)
                result["rationale"] = parsed_result.get("data").get("rationale", "")
        except:
            # 如果解析失败，保留原始响应
            result["message"] = "Failed to parse AI response, but original response is preserved."
            
    except Exception as e:
        # 发生异常时记录错误信息
        result["status"] = "error"
        result["message"] = str(e)
    
    # 将结果转换为JSON字符串并返回
    return json.dumps(result, ensure_ascii=False)
if __name__ == "__main__":
    print(F3_value("The study is a clinical study with a duration of 2 weeks, categorized as sub-chronic."))


