from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Callable

# 数据模型
@dataclass
# DrugInfo类用于存储药物信息
class DrugInfo:
    drug_name: str
    route: str
    data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}

# 处理器接口
# 
class InfoProvider(ABC):
    @abstractmethod
    def process(self, drug_info: DrugInfo) -> DrugInfo:
        """处理药物信息并返回更新后的DrugInfo对象"""
        pass
    
    @property
    def provider_name(self) -> str:
        """返回处理器名称"""
        return self.__class__.__name__

class Pipeline:
    def __init__(self):
        self.steps = []
        self.event_bus = EventBus()
    
    def add_step(self, provider: InfoProvider):
        self.steps.append(provider)
        return self
    
    def process(self, drug_info: DrugInfo) -> DrugInfo:
        result = drug_info
        for step in self.steps:
            try:
                # 发布处理前事件
                self.event_bus.publish(f"before_{step.provider_name}", result)
                
                # 执行处理步骤
                result = step.process(result)
                
                # 发布处理后事件
                self.event_bus.publish(f"after_{step.provider_name}", result)
            except Exception as e:
                result.data['errors'] = result.data.get('errors', [])
                result.data['errors'].append(f"Error in pipeline step {step.provider_name}: {str(e)}")
                self.event_bus.publish("pipeline_error", {"step": step.provider_name, "error": str(e)})
        
        return result

class EventBus:
    def __init__(self):
        self.subscribers = {}
    
    def subscribe(self, event_name: str, callback: Callable):
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        self.subscribers[event_name].append(callback)
    
    def publish(self, event_name: str, data: Any):
        if event_name in self.subscribers:
            for callback in self.subscribers[event_name]:
                callback(data)

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

class ChemicalInfoProvider(InfoProvider):
    def process(self, drug_info: DrugInfo) -> DrugInfo:
        try:
            name = drug_info.drug_name
            json_data = baseinfo.get_chemical_info(name)
            data_dict = json.loads(json_data) if isinstance(json_data, str) else json_data
            
            if data_dict.get('status') == 'success':
                drug_info.data['chemical_info'] = {
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
        except Exception as e:
            drug_info.data['errors'] = drug_info.data.get('errors', [])
            drug_info.data['errors'].append(f"Error in ChemicalInfoProvider: {str(e)}")
        
        return drug_info

class PharmacyInfoProvider(InfoProvider):
    def process(self, drug_info: DrugInfo) -> DrugInfo:
        try:
            name = drug_info.drug_name
            json_data = pharmacy.get_pharmacokinetics(name)
            data_dict = json.loads(json_data) if isinstance(json_data, str) else json_data
            
            if data_dict.get('status') == 'success':
                drug_info.data['pharmacokinetics'] = {
                    "Pharmacokinetics": data_dict.get('Pharmacokinetics'),
                    "Indication": data_dict.get('Indication'),
                    "Pharmacodynamics": data_dict.get('Pharmacodynamics'),
                    "Mechanism of Action": data_dict.get('Mechanism of Action'),
                    "reference_links": data_dict.get('reference_links')
                }
        except Exception as e:
            drug_info.data['errors'] = drug_info.data.get('errors', [])
            drug_info.data['errors'].append(f"Error in PharmacyInfoProvider: {str(e)}")
        
        return drug_info

class ClinicalInfoProvider(InfoProvider):
    def process(self, drug_info: DrugInfo) -> DrugInfo:
        try:
            name = drug_info.drug_name
            route = drug_info.route
            json_data = Clinical.clinical(name, route)
            data_dict = json.loads(json_data) if isinstance(json_data, str) else json_data
            
            if data_dict.get('status') == 'success':
                clinical_data = {
                    "Clinical": data_dict.get('new_generate_content'),
                    "reference_links": data_dict.get('new_citation')
                }
                
                drug_info.data['clinical_info'] = clinical_data
                drug_info.data['dosage_detail'] = data_dict.get('dosage_detail')
                drug_info.data['new_route'] = data_dict.get('route')
        except Exception as e:
            drug_info.data['errors'] = drug_info.data.get('errors', [])
            drug_info.data['errors'].append(f"Error in ClinicalInfoProvider: {str(e)}")
        
        return drug_info

class HazardInfoProvider(InfoProvider):
    def process(self, drug_info: DrugInfo) -> DrugInfo:
        try:
            name = drug_info.drug_name
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
            
            drug_info.data['hazard_info'] = data_output
        except Exception as e:
            drug_info.data['errors'] = drug_info.data.get('errors', [])
            drug_info.data['errors'].append(f"Error in HazardInfoProvider: {str(e)}")
        
        return drug_info

class PoDCalculator(InfoProvider):
    def process(self, drug_info: DrugInfo) -> DrugInfo:
        try:
            # 确保必要的数据已经存在
            if 'clinical_info' not in drug_info.data or 'dosage_detail' not in drug_info.data:
                drug_info.data['errors'] = drug_info.data.get('errors', [])
                drug_info.data['errors'].append("PoDCalculator requires clinical_info and dosage_detail")
                return drug_info
            
            name = drug_info.drug_name
            clinical = drug_info.data['clinical_info'].get('Clinical')
            dosage_detail = drug_info.data['dosage_detail']
            
            json_data = PoD.PoD_value(name, clinical=clinical, dosage_detail=dosage_detail)
            data_dict = json.loads(json_data) if isinstance(json_data, str) else json_data
            
            if data_dict.get('status') == 'success':
                drug_info.data['PoD_info'] = {
                    "PoD_value": data_dict.get('PoD_value'),
                    "PoD_unit": data_dict.get('PoD_unit'),
                    "point_of_departure": data_dict.get('point_of_departure'),
                    "point_of_departure_detail": data_dict.get('point_of_departure_detail')
                }
        except Exception as e:
            drug_info.data['errors'] = drug_info.data.get('errors', [])
            drug_info.data['errors'].append(f"Error in PoDCalculator: {str(e)}")
        
        return drug_info

class FactorsCalculator(InfoProvider):
    def process(self, drug_info: DrugInfo) -> DrugInfo:
        try:
            # 确保必要的数据已经存在
            required_keys = ['clinical_info', 'hazard_info', 'PoD_info']
            for key in required_keys:
                if key not in drug_info.data:
                    drug_info.data['errors'] = drug_info.data.get('errors', [])
                    drug_info.data['errors'].append(f"FactorsCalculator requires {key}")
                    return drug_info
            
            clinical = drug_info.data['clinical_info'].get('Clinical')
            hazard = drug_info.data['hazard_info']
            PoD_detail = drug_info.data['PoD_info']
            
            factors = []
            
            # 计算F3因子
            json_data = F3.F3_value(clinical)
            self._process_factor_result(json_data, factors)
            
            # 计算F4因子
            json_data = F4.F4_value(clinical, hazard)
            self._process_factor_result(json_data, factors)
            
            # 计算F5因子
            json_data = F5.F5_value(PoD_detail, clinical)
            self._process_factor_result(json_data, factors)
            
            # 添加其他因子
            other_factor_data = json.loads(other_factors.other_factors())
            factors.extend(other_factor_data)
            
            drug_info.data['factors'] = factors
        except Exception as e:
            drug_info.data['errors'] = drug_info.data.get('errors', [])
            drug_info.data['errors'].append(f"Error in FactorsCalculator: {str(e)}")
        
        return drug_info
    
    def _process_factor_result(self, json_data, factors_list):
        data_dict = json.loads(json_data) if isinstance(json_data, str) else json_data
        
        if data_dict.get('status') == 'success':
            factors_list.append({
                "factors": data_dict.get('factors'),
                "value": data_dict.get('value'),
                "rationale": data_dict.get('rationale')
            })

class AlphaFactorCalculator(InfoProvider):
    def process(self, drug_info: DrugInfo) -> DrugInfo:
        try:
            # 检查路由是否发生变化
            if 'new_route' not in drug_info.data or drug_info.data['new_route'].lower() == drug_info.route.lower():
                return drug_info
            
            name = drug_info.drug_name
            new_route = drug_info.data['new_route']
            route = drug_info.route
            
            json_data = alpha_factor.a_factor(name, new_route, route)
            data_dict = json.loads(json_data) if isinstance(json_data, str) else json_data
            
            if data_dict.get('status') == 'success':
                a_factor = {
                    "factors": data_dict.get('factors'),
                    "value": data_dict.get('a_factor_value'),
                    "rationale": data_dict.get('a_factor_detail')
                }
                
                # 如果factors已存在，更新α因子
                if 'factors' in drug_info.data:
                    factors = drug_info.data['factors']
                    for i, factor in enumerate(factors):
                        if factor.get("factors") == "α":
                            factors[i] = a_factor
                            break
                    else:
                        factors.append(a_factor)
        except Exception as e:
            drug_info.data['errors'] = drug_info.data.get('errors', [])
            drug_info.data['errors'].append(f"Error in AlphaFactorCalculator: {str(e)}")
        
        return drug_info
    
class DrugProcessor:
    """药物信息处理类，采用模块化设计和管道模式"""
    
    def __init__(self, log_errors=True):
        """
        初始化药物处理器
        
        参数:
            log_errors (bool): 是否记录错误信息
        """
        self.log_errors = log_errors
        self.pipeline = self._create_default_pipeline()
        self.event_bus = self.pipeline.event_bus
        
        # 注册错误日志事件
        if self.log_errors:
            self.event_bus.subscribe("pipeline_error", self._log_error)
    
    def _create_default_pipeline(self) -> Pipeline:
        """创建默认的处理管道"""
        pipeline = Pipeline()
        
        # 添加处理步骤
        pipeline.add_step(ChemicalInfoProvider())
        pipeline.add_step(PharmacyInfoProvider())
        pipeline.add_step(ClinicalInfoProvider())
        pipeline.add_step(HazardInfoProvider())
        pipeline.add_step(PoDCalculator())
        pipeline.add_step(FactorsCalculator())
        pipeline.add_step(AlphaFactorCalculator())
        
        return pipeline
    
    def _log_error(self, error_data):
        """记录错误信息"""
        print(f"Error in {error_data['step']}: {error_data['error']}")
    
    def add_processor(self, processor: InfoProvider, position: Optional[int] = None):
        """
        添加新的处理器到管道中
        
        参数:
            processor: 实现InfoProvider接口的处理器
            position: 插入位置，None表示添加到末尾
        """
        if position is None:
            self.pipeline.add_step(processor)
        else:
            self.pipeline.steps.insert(position, processor)
    
    def remove_processor(self, processor_name: str):
        """
        从管道中移除处理器
        
        参数:
            processor_name: 处理器名称
        """
        self.pipeline.steps = [step for step in self.pipeline.steps 
                              if step.provider_name != processor_name]
    
    def process_drug(self, name, route, APID=None, api_id=None):
        """
        处理药物的完整流程
        
        参数:
            name (str): 药物名称
            route (str): 给药途径
            APID: API ID
            api_id: 另一个API ID
            
        返回:
            dict: 包含所有处理结果的字典
        """
        try:
            # 创建初始药物信息对象
            drug_info = DrugInfo(drug_name=name, route=route)
            
            # 添加额外信息
            if APID:
                drug_info.data['APID'] = APID
            if api_id:
                drug_info.data['api_id'] = api_id
            
            # 执行处理管道
            result = self.pipeline.process(drug_info)
            
            # 构建最终结果
            final_result = {
                "APID": result.data.get('APID'),
                "api_id": result.data.get('api_id'),
                "drug_name": result.drug_name,
                "route": result.route,
                "chemical_info": result.data.get('chemical_info', {}),
                "pharmacokinetics": result.data.get('pharmacokinetics', {}),
                "clinical_info": result.data.get('clinical_info', {}),
                "hazard_info": result.data.get('hazard_info', []),
                "PoD_info": result.data.get('PoD_info', {}),
                "factors": result.data.get('factors', []),
                "status": "success" if 'errors' not in result.data or not result.data['errors'] else "partial_success",
                "message": ""
            }
            
            # 如果有错误，添加到消息中
            if 'errors' in result.data and result.data['errors']:
                final_result["message"] = "; ".join(result.data['errors'])
            
            return final_result
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
            if self.log_errors:
                print(f"Error saving result: {str(e)}")
            return False

if __name__ == '__main__':
    # 创建药物处理器实例
    processor = DrugProcessor()
    
    # 可选：添加自定义处理器
    # processor.add_processor(CustomProcessor())
    
    # 可选：移除不需要的处理器
    # processor.remove_processor("HazardInfoProvider")
    # 处理药物
    # result = processor.process_drug("Papain", "Oral", "B00088", "402")
    import pandas as pd
    df = pd.read_excel('APID_with_temple2.xlsx')
    # 读取df中每一行的数据
    result_list = []
    for index, row in df.iterrows():
        # 读取每一行的数据
        drug_name = row['ingredient']
        route = row['route']
        APID = row['APID']
        api_id = row['id']
        # 处理药物
        result = processor.process_drug(drug_name, route, APID, api_id)
        result_list.append(result)
    # 保存结果到jsonl文件中
    with open('report_result.jsonl', 'w') as f:
        for result in result_list:
            f.write(json.dumps(result,ensure_ascii=False)+'\n')
    

