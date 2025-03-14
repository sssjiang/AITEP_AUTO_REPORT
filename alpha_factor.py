from utils.llm_utils import AITEP
import json
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import pandas as pd
import concurrent.futures
# especial for daily_med need to upgrade
# aliyun max_latest_version
def is_valid_data(data):
    """
    检查数据是否有效
    
    参数:
        data: 任意类型的数据
        
    返回:
        bool: 数据是否有效
    """
    # 检查是否为 None
    if data is None:
        return False
    
    # 检查是否为 NaN (numpy.nan 或 pandas.NA)
    if pd.isna(data) or isinstance(data, float) and np.isnan(data):
        return False
    
    # 如果是字符串，检查是否为空或只包含空白字符
    if isinstance(data, str) and not data.strip():
        return False
    
    # 如果是列表、字典或集合，检查是否为空
    if isinstance(data, (list, dict, set)) and not data:
        return False
        
    return True
prompt="""
## Task Description
Calculate the correction factor according to following guidelines.

## Required Input
- **Drug name**: [Drug name]
- **Source administration route**: [Source route] (oral/intravenous/inhalation/etc.)
- **Target administration route**: [Target route] (oral/intravenous/inhalation/etc.)

### **Content**  
**Input:**  
{{CONTENT}}  
**End**

## Process
step 1: Deep Search website and retrieve bioavailability data for both administration routes for the drug,if bioavailability data is not available, please provide a reasonable bioavailability range estimate based on the following factors:
1. **General Bioavailability Hierarchy**:
    Typical bioavailability hierarchy by administration route (from highest to lowest systemic exposure):
    - Intravenous (100% by definition)
    - Inhalation (generally 80-100% for small molecules)
    - Intramuscular (generally 75-100%)
    - Subcutaneous (generally 75-100%)
    - Oral (highly variable: ~5-100%)
    - Sublingual/Buccal (generally 30-70%)
    - Rectal (generally 30-50%)
    - Transdermal (generally 5-25%)
    - Topical (generally <5%)

2. **Physicochemical Property Analysis**:
   - Evaluate drug lipophilicity/hydrophilicity (LogP value)
   - Molecular weight and its impact on membrane permeability
   - Ionization state and pKa effects at physiological pH
   - Number of hydrogen bond donors/acceptors affecting absorption

3. **Structural Analogy Assessment**:
   - Identify structurally similar drugs with known bioavailability
   - Compare key functional groups and metabolic sites
   - Consider bioavailability trends in the same drug class

4. **Metabolic Factor Consideration**:
   - Assess potential extent of first-pass effect
   - Identify major metabolic pathways (CYP450 system, etc.)
   - Consider prodrug design impact on bioavailability
   - Analyze potential intestinal/hepatic metabolism extent

5. **Physiological Pharmacokinetic Considerations**:
   - Evaluate likely absorption sites and mechanisms
   - Consider transporter-mediated absorption or efflux possibilities
   - Analyze drug stability in gastrointestinal environment
   - Consider enteric properties and release characteristics affecting absorption

6. **Uncertainty Statement**:
   - Clearly indicate limitations of the estimated range
   - Emphasize this is a theoretical estimate not for clinical decisions
   - Recommend actual bioavailability studies when possible

Based on the above analysis, provide a reasonable bioavailability range estimate, stating the confidence level of this estimate and influencing factors.

step 2: Calculate the Adjustment Factor for each administration route based on the bioavailability range estimate or data using the following rules:
Adjustment Factor only have 4 values: 100, 10, 2, 1.
## Adjustment Rules
| Bioavailability Range | Adjustment Factor |
|-----------------------|------------------|
| <1%                   | 100              |
| ≥1% and <50%          | 10               |
| ≥50% and <90%         | 2                |
| ≥90%                  | 1                |


step 3: Calculate the FINAL correction factor (a_factor_value) using EXACTLY this formula:
a_factor_value =  Source route Adjustment Factor / Target route Adjustment Factor
## Response Format
```json
{   
    "source_route_bioavailability": "[Value or range]%",
    "source_route_adjustment_factor": [100, 10, 2, 1],
    "target_route_bioavailability": "[Value or range]%",
    "target_route_adjustment_factor": [100, 10, 2, 1],
    "a_factor_value": numerical value,
    "a_factor_detail": "detailed process with step-by-step explanation"
}
```
Example
Input:

Drug name: Aspirin
Source administration route: Oral
Target administration route: Intravenous
Output:
```json
{
    "source_route_bioavailability": "80%",
    "source_route_adjustment_factor": 2,
    "target_route_bioavailability": "100%",
    "target_route_adjustment_factor": 1,
    "a_factor_value": 2,
    "a_factor_detail": "Aspirin oral bioavailability: 80% (Source route Adjustment Factor: 2). Intravenous bioavailability: 100% (Target route Adjustment Factor: 1). a_factor_value = Source route Adjustment Factor / Target route Adjustment Factor = 2. So 2 is final a_factor_value."
}
```
Important Notes
a_factor_value value from 0.01 to 100.
consider specific drug characteristics and clinical context.
The response will contain ONLY the JSON output with no additional text.
"""
def a_factor(name,target_route,source_route):
    default_result = {
        "factor": "α",
        "source_route_bioavailability": "",
        "source_route_adjustment_factor": None,
        "target_route_bioavailability": "",
        "target_route_adjustment_factor": None,
        "a_factor_value": None,
        "a_factor_detail": "",
        "status": "success",
        "message": "",
        "GAI_original": ""
    }
    try:
        main_content_json={
                    "Drug_name":name,
                    "Target administration route":target_route,
                    "Source administration route":source_route
        }
        format_prompt = prompt.replace("{{CONTENT}}", json.dumps(main_content_json, indent=4))
        ai= AITEP()
        result_json = ai.run_llm(file_id=None, llm_model="qwen-plus", prompt=format_prompt)
        default_result["GAI_original"] = result_json
        result_json = result_json.get("data")
        for key in result_json:
            if key in default_result and key not in ["status", "message"]:
                default_result[key] = result_json[key]
    except Exception as e:
        default_result["status"] = "error"
        default_result["message"] = f"Error processing row: {str(e)}"
    return json.dumps(default_result, ensure_ascii=False)


if __name__ == "__main__":
    print(a_factor("Aspirin","Oral","Intravenous"))
    



    