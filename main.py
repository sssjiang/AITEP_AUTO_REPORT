import os
import json
import baseinfo
import pharmacy
import hazards
import Clinical
import PoD
import F3
import F4
import F5
import other_factors

def get_chemical_info(name):
    # 调用Pubmed的process_chemical函数
    json_data = baseinfo.get_chemical_info(name)
    data_dict = json.loads(json_data)
    if data_dict.get('status') == 'success':
        #  取出 Synonyms,CAS Number,Molecular Formula,Molecular Weight,SMILES,InChI,InChIKey
        data_out={
            "drug_name": data_dict.get('drug_name'),
            "Synonyms": data_dict.get('Synonyms'),
            "CAS Number": data_dict.get('CAS Number'),
            "Molecular Formula": data_dict.get('Molecular Formula'),
            "Molecular Weight": data_dict.get('Molecular Weight'),
            "SMILES": data_dict.get('SMILES'),
            "InChI": data_dict.get('InChI'),
            "InChIKey": data_dict.get('InChIKey'),
            "reference_links": data_dict.get('reference_links')
        }
        return data_out
    else:
        print("No search results")
        return None
# llm输入药名直接生成 Pharmacokinetics["Absorption","Distribution","Metabolism","Excretion"],Indication,Pharmacodynamics,Mechanism of Action
def get_pharmacokinetics(name):
    json_data = pharmacy.get_pharmacokinetics(name)
    data_dict = json.loads(json_data)
    if data_dict.get('status') == 'success':
        #  取出 Pharmacokinetics,Indication,Pharmacodynamics,Mechanism of Action
        data_out={
            "Pharmacokinetics": data_dict.get('Pharmacokinetics'),
            "Indication": data_dict.get('Indication'),
            "Pharmacodynamics": data_dict.get('Pharmacodynamics'),
            "Mechanism of Action": data_dict.get('Mechanism of Action'),
            "reference_links": data_dict.get('reference_links')
        }
    return data_out


# AI search 结果
def get_hazard_info(name): 
    json_data=hazards.all_toxicities(name)
    data_dict = json.loads(json_data) 
    data_output = []
    if data_dict.get('status') == 'success':
        for row in data_dict.get('harzard_identification'):
            data_dict = {
                "param1": row.get('toxicity_type'),
                "param2": row.get('result'),
                "param3": row.get('result_detail'),
                "reference_links": row.get('reference_links')
            }
            data_output.append(data_dict)
    # 同时data_output要提供给calculate_factors
    return data_output

def get_clinical_info(name,route):
    json_data=Clinical.clinical(name,route)
    data_dict = json.loads(json_data)
    if data_dict.get('status') == 'success':
        #  取出 new_generate_content,new_citation
        output_data={
            "Clinical":data_dict.get('new_generate_content'),
            "reference_links":data_dict.get('new_citation')
        }
        dosage_detail=data_dict.get('dosage_detail')
    # 同时 Clinical要提供给calculate_factors, dosage_detail要提供给calculate_PoD
    return {
        "Clinical":output_data,
        "dosage_detail":dosage_detail
    }

def calculate_PoD(name,clinical,dosage_detail):
    json_data=PoD.PoD_value(name,clinical=clinical,dosage_detail=dosage_detail)
    data_dict = json.loads(json_data)
    print("test",data_dict)
    if data_dict.get('status') == 'success':
        #  取出 PoD_value,PoD_unit,point_of_departure,point_of_departure_detail
        output_data={
            "PoD_value":data_dict.get('PoD_value'),
            "PoD_unit":data_dict.get('PoD_unit'),
            "point_of_departure":data_dict.get('point_of_departure'),
            "point_of_departure_detail":data_dict.get('point_of_departure_detail')
        }
    # 同时output_data要提供给calculate_factors
    return output_data

def calculate_factors(clinical,hazard,PoD_detail):
    json_data=F3.F3_value(clinical)
    data_dict = json.loads(json_data)
    factors=[]
    if data_dict.get('status') == 'success':
        #  取出 value,rationale
        output_data={
             "factors":data_dict.get('factors'),
            "value":data_dict.get('value'),
            "rationale":data_dict.get('rationale')
        }
        factors.append(output_data)
    json_data=F4.F4_value(clinical,hazard)
    data_dict = json.loads(json_data)
    if data_dict.get('status') == 'success':
        #  取出 value,rationale
        output_data={
            "factors":data_dict.get('factors'),
            "value":data_dict.get('value'),
            "rationale":data_dict.get('rationale')
        }
        factors.append(output_data)
    json_data=F5.F5_value(PoD_detail,clinical)
    data_dict = json.loads(json_data)
    if data_dict.get('status') == 'success':
        #  取出 value,rationale
        output_data={
             "factors":data_dict.get('factors'),
            "value":data_dict.get('value'),
            "rationale":data_dict.get('rationale')
        }
        factors.append(output_data)
    factors.extend(json.loads(other_factors.other_factors()))
    return factors
def total_run(name,route):
    # 获取基本信息
    chemical_info=get_chemical_info(name)
    # 获取药代动力学信息
    pharmacokinetics=get_pharmacokinetics(name)
    # 获取临床信息
    clinical_info=get_clinical_info(name,route)
    # 获取危害信息
    hazard_info=get_hazard_info(name)
    # 获取PoD信息
    PoD_info=calculate_PoD(name,clinical_info.get('Clinical').get('Clinical'),clinical_info.get('dosage_detail'))
    # 计算因子
    factors=calculate_factors(clinical_info.get('Clinical').get('Clinical'),hazard_info,PoD_info)
    return {
        "chemical_info":chemical_info,
        "pharmacokinetics":pharmacokinetics,
        "clinical_info":clinical_info.get('Clinical'),
        "hazard_info":hazard_info,
        "PoD_info":PoD_info,
        "factors":factors
    }


if __name__ == '__main__':
    # clinical="### Clinical Therapeutic Doses\n\n| Species | Treatment | Route | Dosage |\n|---------|-----------|--------|---------|\n| Adults | HIV-1 infection | Oral | 600 mg once daily or 300 mg twice daily |\n| Pediatric patients (≥14 kg) | HIV-1 infection | Oral | Dose calculated based on body weight, not exceeding 600 mg daily |\n\n<br>\n\n### Adverse Effects\n\nAbacavir can cause serious hypersensitivity reactions, lactic acidosis, severe hepatomegaly with steatosis, and immune reconstitution syndrome. Common side effects include nausea, vomiting, fever, and fatigue.\n\n<br>\n\n### Warning\n\nAbacavir should be used with caution in patients with a history of cardiovascular disease due to an increased risk of myocardial infarction. It is also important to monitor for signs of lactic acidosis and severe hepatomegaly with steatosis.\n\n<br>\n\n### Box warning\n\n**Black Box Warning:**\n\nSerious and sometimes fatal hypersensitivity reactions have occurred with abacavir. Patients who carry the HLA-B*5701 allele are at a higher risk of these reactions. Abacavir is contraindicated in patients with a prior hypersensitivity reaction to abacavir or in those with the HLA-B*5701 allele.\n\n<br>\n\n### Clinical Critical Effects\n\nThe critical or lead effects of abacavir in clinical data were the treatment of HIV-1 infection[1][3]."
    # hazard=[{'param1': 'Genotoxicant', 'param2': 'Yes', 'param3': 'The genotoxic potential of abacavir is supported by multiple studies, including those from peer-reviewed scientific literature. While regulatory authorities have not explicitly classified it as a genotoxicant, the evidence from animal and in vitro studies suggests that abacavir can induce genetic damage, particularly in combination with other drugs.'}, {'param1': 'Carcinogen', 'param2': 'Unknown', 'param3': "While abacavir has shown carcinogenic effects in animal studies, it is not classified as a carcinogen by major regulatory bodies. The evidence from animal studies suggests potential carcinogenic activity, but this is not sufficient for a definitive classification as a human carcinogen. Therefore, the result is 'Unknown' due to conflicting evidence and lack of human epidemiological data."}, {'param1': 'Reproductive/Developmental Toxicant', 'param2': 'No', 'param3': 'While animal studies suggest potential developmental toxicity, extensive human data from pregnancy registries do not indicate an increased risk of major birth defects. Therefore, the risk in humans is considered low based on available evidence.'}, {'param1': 'Highly Sensitizing Potential', 'param2': 'Yes', 'param3': 'The FDA and other regulatory bodies have issued warnings about the hypersensitivity potential of abacavir, particularly in individuals with the HLA-B*5701 allele. Peer-reviewed literature consistently supports the high sensitizing potential of abacavir, making it a well-documented risk.'}]
    # PoD_detail="{'PoD_value': 0.5, 'PoD_unit': 'mg/kg/day', 'point_of_departure': '0.5 mg/kg/day', 'point_of_departure_detail': 'The PoD was determined based on the NOAEL of 50 mg/kg/day from a 90-day oral toxicity study in rats, applying an uncertainty factor of 100.'}"
    # print(calculate_factors(clinical,hazard,PoD_detail))
    result=(total_run("Abacavir", "Oral"))
    with open('report_result.json', 'w') as f:
        json.dump(result, f, indent=4,ensure_ascii=False)






