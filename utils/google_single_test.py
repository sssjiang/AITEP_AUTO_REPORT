
import json
import llm_utils
# 1. Google Custom Search API（推荐）
# 这是 Google 官方提供的搜索 API，需要：
# 创建 Google Cloud Project
# 获取 API Key
# 创建自定义搜索引擎（CSE）
from googleapiclient.discovery import build
# 使用示例
import configparser
# 读取配置文件
config = configparser.ConfigParser()
config.read('api.ini')
API_KEY = config['google']['API_KEY']
CSE_ID = config['google']['CSE_ID']


prompt="""
### Task
Analyze the title and snippet to:
1. Determine relevance to chemical_name and chemical_route (yes/no)
2. Identify if content is from product documentation (yes/no)

### Output Format
{
    "relation": "yes/no",
    "production": "yes/no",
    "reason": "Brief explanation"
}

### Example
Input:
- Title: {{title}}
- Snippet: {{snippet}}
- chemical_name: {{chemical_name}}
- chemical_route: {{chemical_route}}

```json
Output:
{
    "relation": "yes",
    "production": "yes",
    "reason": "Title contains topical medication info (ZOVIRAX® Ointment) matching chemical_route 'Topical'"
}
```
### Notes
- Return JSON only
- Keep reason concise

"""
# google search
def google_search(query, **kwargs):
    api_key=API_KEY
    cse_id=CSE_ID
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=query, cx=cse_id, **kwargs).execute()
    return res['items']
# Aliyun 大模型 check 链接内容是否和药物相关 标记
def aliyun_check(origin_info,chemical_name,chemical_route):
    for result in origin_info:
        title=result["title"]
        snippet=result["snippet"]
        # response=AI_check_call(title,snippet,chemical_name,chemical_route)
        ai=llm_utils.AITEP()
        formatted_prompt = prompt.replace("{{title}}", title)
        formatted_prompt = formatted_prompt.replace("{{snippet}}", snippet)
        formatted_prompt = formatted_prompt.replace("{{chemical_name}}", chemical_name)
        formatted_prompt = formatted_prompt.replace("{{chemical_route}}", chemical_route)
        response = ai.run_llm(file_id=None, llm_model="qwen-plus", prompt=formatted_prompt)
        json_data=response.get("data")
        result["GAI_origin"]=response
        result["GAI_relation"]=json_data["relation"]
        result["GAI_production"]=json_data["production"]
        result["GAI_reason"]=json_data["reason"]
    return origin_info


# 域名标记 link处理
def domain_filter(origin_info):
    for result in origin_info:
        link=result["link"]
        if link:
            if "dailymed.nlm" in link:
                result["func_domain"]="dailymed"
            elif "drugs.com" in link:
                result["func_domain"]="drugs.com" 
            else:
                result["func_domain"]="others"              

# 标记功能
def tag_function(chemical_name, chemical_route, origin_info):
    origin_info= aliyun_check(origin_info, chemical_name, chemical_route)
    origin_info = domain_filter(origin_info)
    json_result=json.dumps(origin_info, ensure_ascii=False)
    return json_result

 
def main(ingredient,route):
    searchword=f"{ingredient} dailymed"
    results=google_search(searchword)
    filter_result=tag_function(ingredient,route,results)
    return filter_result




# 使用示例
if __name__ == "__main__":
    print(main("aspirin","oral"))