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
import alpha_factor
class DrugProcessor:
    """药物信息处理类，封装了药物信息获取和分析的所有功能"""
    
    def __init__(self, log_errors=True):
        """
        初始化药物处理器
        
        参数:
            log_errors (bool): 是否记录错误信息
        """
        self.log_errors = log_errors
    
    def _handle_error(self, error_msg, default_return=None):
        """处理错误并返回默认值"""
        if self.log_errors:
            print(error_msg)
        return default_return
    
    def get_chemical_info(self, name):
        """获取药物的化学信息"""
        try:
            json_data = baseinfo.get_chemical_info(name)
            data_dict = json.loads(json_data) if isinstance(json_data, str) else json_data
            
            if data_dict.get('status') == 'success':
                return {
                    "drug_name": data_dict.get('drug_name'),
                    "Synonyms": data_dict.get('Synonyms'),
                    "CAS Number": data_dict.get('CAS Number'),
                    "Molecular Formula": data_dict.get('Molecular Formula'),
                    "Molecular Weight": data_dict.get('Molecular Weight'),
                    "Smiles": data_dict.get('Smiles'),
                    "InchI Key": data_dict.get('InchI Key'),
                    "IUPAC Name": data_dict.get('IUPAC Name'),
                    "Description": data_dict.get('Description'),
                    "ATC Code": data_dict.get('ATC Code'),
                    "Pharmacotherapeutic Group": data_dict.get('Pharmacotherapeutic Group'),
                    "Appearance": data_dict.get('Appearance'),
                    "Solubility": data_dict.get('Solubility'),
                    "reference_links": data_dict.get('reference_links')
                }
            return self._handle_error(f"No chemical info found for {name}", {})
        except Exception as e:
            return self._handle_error(f"Error getting chemical info: {str(e)}", {})
    
    def get_pharmacokinetics(self, name):
        """获取药物的药代动力学信息"""
        try:
            json_data = pharmacy.get_pharmacokinetics(name)
            data_dict = json.loads(json_data) if isinstance(json_data, str) else json_data
            
            if data_dict.get('status') == 'success':
                return {
                    "Pharmacokinetics": data_dict.get('Pharmacokinetics'),
                    "Indication": data_dict.get('Indication'),
                    "Pharmacodynamics": data_dict.get('Pharmacodynamics'),
                    "Mechanism of Action": data_dict.get('Mechanism of Action'),
                    "reference_links": data_dict.get('reference_links')
                }
            return self._handle_error(f"No pharmacokinetics found for {name}", {})
        except Exception as e:
            return self._handle_error(f"Error getting pharmacokinetics: {str(e)}", {})
    
    def get_hazard_info(self, name):
        """获取药物的危害信息"""
        try:
            json_data = hazards.all_toxicities(name)
            data_dict = json.loads(json_data) if isinstance(json_data, str) else json_data
            
            data_output = []
            if data_dict.get('status') == 'success':
                for row in data_dict.get('harzard_identification', []):
                    data_output.append({
                        "param1": row.get('toxicity_type'),
                        "param2": row.get('result'),
                        "param3": row.get('result_detail'),
                        "reference_links": row.get('reference_links')
                    })
            return data_output
        except Exception as e:
            return self._handle_error(f"Error getting hazard info: {str(e)}", [])
    
    def get_clinical_info(self, name, route):
        """获取药物的临床信息"""
        try:
            json_data = Clinical.clinical(name, route)
            data_dict = json.loads(json_data) if isinstance(json_data, str) else json_data
            
            if data_dict.get('status') == 'success':
                output_data = {
                    "Clinical": data_dict.get('new_generate_content'),
                    "reference_links": data_dict.get('new_citation')
                }
                dosage_detail = data_dict.get('dosage_detail')
                new_route=data_dict.get('route')
                
                return {
                    "Clinical": output_data,
                    "dosage_detail": dosage_detail,
                    "route":new_route
                }
            return self._handle_error(f"No clinical info found for {name}", {})
        except Exception as e:
            return self._handle_error(f"Error getting clinical info: {str(e)}", {})
    
    def calculate_PoD(self, name, clinical, dosage_detail):
        """计算PoD值"""
        try:
            json_data = PoD.PoD_value(name, clinical=clinical, dosage_detail=dosage_detail)
            data_dict = json.loads(json_data) if isinstance(json_data, str) else json_data
            
            if data_dict.get('status') == 'success':
                return {
                    "PoD_value": data_dict.get('PoD_value'),
                    "PoD_unit": data_dict.get('PoD_unit'),
                    "point_of_departure": data_dict.get('point_of_departure'),
                    "point_of_departure_detail": data_dict.get('point_of_departure_detail')
                }
            return self._handle_error(f"Failed to calculate PoD for {name}", {})
        except Exception as e:
            return self._handle_error(f"Error calculating PoD: {str(e)}", {})
    
    def calculate_factors(self, clinical, hazard, PoD_detail):
        """计算因子"""
        def process_factor_result(json_data, factors_list):
            """
            处理因子计算的返回结果
            
            Args:
                json_data: 因子计算函数返回的JSON数据
                factors_list: 存储因子的列表 处理 F3, F4, F5 因子
            """
            data_dict = json.loads(json_data) if isinstance(json_data, str) else json_data
            
            if data_dict.get('status') == 'success':
                factors_list.append({
                    "factors": data_dict.get('factors'),
                    "value": data_dict.get('value'),
                    "rationale": data_dict.get('rationale')
                })
        factors = []
        try:
            # 计算F3因子
            json_data = F3.F3_value(clinical)
            process_factor_result(json_data, factors)
            
            # 计算F4因子
            json_data = F4.F4_value(clinical, hazard)
            process_factor_result(json_data, factors)
            
            # 计算F5因子
            json_data = F5.F5_value(PoD_detail, clinical)
            process_factor_result(json_data, factors)
            
            # 添加其他因子 F1, F2, F6, a
            other_factor_data = json.loads(other_factors.other_factors())
            factors.extend(other_factor_data)
            
            return factors
        except Exception as e:
            return self._handle_error(f"Error calculating factors: {str(e)}", [])


    def calculation_a_factor(self,name,new_route,route)->dict:
        """计算α因子"""
        try:
            json_data = alpha_factor.a_factor(name,new_route,route)
            data_dict = json.loads(json_data) if isinstance(json_data, str) else json_data
            
            if data_dict.get('status') == 'success':
                return {
                    "factors": data_dict.get('factors'),
                    "value": data_dict.get('a_factor_value'),
                    "rationale": data_dict.get('a_factor_detail')
                }
            return self._handle_error(f"Failed to calculate α factor", {})
        except Exception as e:
            return self._handle_error(f"Error calculating α factor: {str(e)}", {})
    def process_drug(self, name, route,APID,api_id):
        """
        处理药物的完整流程
        
        参数:
            name (str): 药物名称
            route (str): 给药途径
            
        返回:
            dict: 包含所有处理结果的字典
        """

        try:
            # 获取基本信息
            chemical_info = self.get_chemical_info(name)
            
            # 获取药代动力学信息
            pharmacokinetics = self.get_pharmacokinetics(name)
            
            # 获取临床信息
            clinical_info = self.get_clinical_info(name, route)
            
            # 获取危害信息
            hazard_info = self.get_hazard_info(name)
            
            # 获clinical文本信息不包含 link
            clinical_data = clinical_info.get('Clinical', {}).get('Clinical')
            dosage_detail = clinical_info.get('dosage_detail')
            PoD_info = self.calculate_PoD(name, clinical_data, dosage_detail)
            # 计算因子
            factors = self.calculate_factors(clinical_data, hazard_info, PoD_info)
            new_route=clinical_info.get('route')
            
            if new_route.lower() != route.lower():
                 # 重新计算 α 因子
                a_factor = self.calculation_a_factor(name,new_route,route)
                # 在factors列表中查找并更新α因子
                for i, factor in enumerate(factors):
                    if factor.get("factors") == "α":
                        # 用新计算的α因子替换原来的值
                        factors[i] = a_factor
                        break
                else:
                    # 如果没有找到α因子，则添加到列表中
                    factors.append(a_factor)

            # 构建结果
            result = {
                "APID":APID,
                "api_id":api_id,
                "drug_name": name,
                "route": route,
                "chemical_info": chemical_info,
                "pharmacokinetics": pharmacokinetics,
                "clinical_info": clinical_info.get('Clinical'),
                "hazard_info": hazard_info,
                "PoD_info": PoD_info,
                "factors": factors,
                "status": "success",
                "message": ""
            }
            
            return result
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error processing drug {name}: {str(e)}",
                "drug_name": name
            }
    
    def save_result(self, result, filename='report_result.json'):
        """保存处理结果到JSON文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            return self._handle_error(f"Error saving result: {str(e)}", False)


if __name__ == '__main__':
    # 创建药物处理器实例
    processor = DrugProcessor()
    
    # 处理药物
    result = processor.process_drug("Myrtol", "Oral","B00088","402")
    
    # 保存结果
    processor.save_result(result,filename='report_result_2.json')
