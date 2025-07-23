import os
import json
import hashlib
import requests
import configparser
import re
from googleapiclient.discovery import build
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MessageRole, BingGroundingTool
from azure.identity import ClientSecretCredential
class BaseSearchWithCache:
    """搜索引擎的基类，提供缓存功能"""
    
    def __init__(self, cache_path):
        """
        初始化基础搜索类
        :param cache_path: 缓存文件路径
        """
        self.cache_path = cache_path
        
    def _load_cache(self, key):
        """加载缓存文件"""
        file = "{}/{}".format(self.cache_path, key)
        if os.path.exists(file):
            print("Cache Found: {}".format(key))
            with open(file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def _save_cache(self, key, data):
        """保存缓存到文件"""
        file = "{}/{}".format(self.cache_path, key)
        # 如果目录不存在，则创建
        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _generate_cache_key(self, query):
        """生成缓存的键值"""
        return hashlib.md5(query.encode('utf-8')).hexdigest()
    
    def search(self, query, force_refresh=False):
        """
        搜索并缓存结果（子类需要实现）
        """
        raise NotImplementedError("子类必须实现search方法")




class BochaSearch(BaseSearchWithCache):
    """使用Bocha API进行搜索"""
    
    def __init__(self, cache_path='./cached'):
        """
        初始化Bocha搜索类
        :param cache_path: 缓存文件路径
        """
        super().__init__(cache_path)
        # 读取配置文件
        config = configparser.ConfigParser()
        config.read('api.ini')
        self.api_key = config['Bocha']['ACCESS_TOKEN']

    def search(self, query, force_refresh=False):
        """
        搜索Bocha并缓存结果
        :param query: 搜索关键词
        :param force_refresh: 是否强制刷新缓存
        :return: 搜索结果
        """
        cache_key = self._generate_cache_key(query)

        # 如果缓存中存在结果且不强制刷新，直接返回缓存结果
        if not force_refresh:
            cached_data = self._load_cache(cache_key)
            if cached_data is not None:
                # 如果缓存已经是字符串形式，直接返回
                if isinstance(cached_data, str):
                    return cached_data
                # 如果缓存是对象形式，转换为JSON字符串
                else:
                    return json.dumps(cached_data, ensure_ascii=False)

        # 调用Bocha API
        print("调用Bocha API搜索...")
        url = "https://api.bochaai.com/v1/web-search"
        payload = json.dumps({
          "query": query,
          "freshness": "oneYear",
          "summary": True,
          "count": 8
        })
        headers = {
          'Authorization': f'Bearer {self.api_key}',
          'Content-Type': 'application/json'
        }
        try:
            response = requests.request("POST", url, headers=headers, data=payload)
            response.raise_for_status()  # 抛出异常如果请求失败
            
            if response.status_code == 200:
                res = response.json()
                rows = res.get('data', {}).get('webPages', {}).get('value', [])
                data = []
                for row in rows:
                    data.append({
                        "url": row.get('url'),
                        "snippet": row.get('snippet'),
                        "summary": row.get('summary'),
                    })
                
                # 转换为JSON字符串
                json_result = json.dumps(data, ensure_ascii=False)
                # 保存到缓存
                self._save_cache(cache_key, json_result)
                
                return json_result
        except Exception as e:
            error_result = {
                "status": "error",
                "message": str(e),
                "query": query
            }
            return json.dumps(error_result, ensure_ascii=False)


class AzureSearch(BaseSearchWithCache):
    """使用Azure AI Projects API进行搜索"""
    
    def __init__(self, cache_path='./azure_search_cached'):
        """
        初始化Azure搜索类
        :param cache_path: 缓存文件路径
        """
        super().__init__(cache_path)
        # 读取配置文件
        config = configparser.ConfigParser()
        config.read('api.ini')
        self.client_id = config['azure']['client_id']
        self.tenant_id = config['azure']['tenant_id']
        self.client_secret = config['azure']['value']
        self.project_connect_string = config['azure']['project_connet_string']
        
        # 去掉project_connect_string前后的引号（如果有）
        if self.project_connect_string.startswith('"') and self.project_connect_string.endswith('"'):
            self.project_connect_string = self.project_connect_string[1:-1]
        
        # 初始化凭据和客户端
        self.credential = ClientSecretCredential(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        
        self.project_client = None  # 将在search方法中懒加载

    def search(self, query, force_refresh=False):
        """
        调用Azure AI Projects API并缓存结果
        :param query: 搜索关键词
        :param force_refresh: 是否强制刷新缓存
        :return: API响应结果
        """
        cache_key = self._generate_cache_key(query)

        # 如果缓存中存在结果且不强制刷新，直接返回缓存结果
        if not force_refresh:
            cached_data = self._load_cache(cache_key)
            if cached_data is not None:
                # 如果缓存已经是字符串形式，直接返回
                if isinstance(cached_data, str):
                    return cached_data
                # 如果缓存是对象形式，转换为JSON字符串
                else:
                    return json.dumps(cached_data, ensure_ascii=False)

        # 调用Azure AI Projects API
        print("调用Azure AI Projects API搜索...")
        
        try:
            # 懒加载客户端
            if self.project_client is None:
                self.project_client = AIProjectClient.from_connection_string(
                    credential=self.credential,
                    conn_str=self.project_connect_string
                )
            
            # 获取Bing搜索连接
            bing_connection = self.project_client.connections.get(connection_name="groundsearch")
            conn_id = bing_connection.id
            
            # 初始化Bing工具
            bing = BingGroundingTool(connection_id=conn_id)
            
            # 创建代理和处理助手运行
            with self.project_client:
                # 创建代理
                agent = self.project_client.agents.create_agent(
                    model="gpt-35-turbo",
                    name="search-assistant",
                    instructions="You are a helpful assistant that provides accurate information",
                    tools=bing.definitions,
                )
                
                # 创建线程
                thread = self.project_client.agents.create_thread()
                
                # 创建消息
                self.project_client.agents.create_message(
                    thread_id=thread.id,
                    role=MessageRole.USER,
                    content=query,
                )
                
                # 创建并处理代理运行
                run = self.project_client.agents.create_and_process_run(
                    thread_id=thread.id, 
                    agent_id=agent.id
                )
                
                # 获取响应
                response_message = self.project_client.agents.list_messages(
                    thread_id=thread.id
                ).get_last_message_by_role(MessageRole.AGENT)
                
                # 构建结果
                result = {
                    "status": "success" if run.status == "completed" else "error",
                    "query": query,
                    "content": [],
                    "citations": []
                }
                
                if response_message:
                    # 添加文本内容
                    for text_message in response_message.text_messages:
                        result["content"].append(text_message.text.value)
                    
                    # 添加引用
                    for annotation in response_message.url_citation_annotations:
                        result["citations"].append({
                            "title": annotation.url_citation.title,
                            "url": annotation.url_citation.url
                        })
                
                # 删除代理
                self.project_client.agents.delete_agent(agent.id)
                
                # 保存到缓存
                result_json = json.dumps(result, ensure_ascii=False)
                self._save_cache(cache_key, result_json)
                return result_json
                
        except Exception as e:
            error_result = {
                "status": "error",
                "message": str(e),
                "query": query
            }
            return json.dumps(error_result, ensure_ascii=False)
class PerplexitySearch(BaseSearchWithCache):
    """使用Perplexity API进行搜索"""
    
    def __init__(self, cache_path='./perplexity_cached'):
        """
        初始化Perplexity搜索类
        :param cache_path: 缓存文件路径
        """
        super().__init__(cache_path)
        # 读取配置文件
        config = configparser.ConfigParser()
        # 获取当前文件所在目录的路径
        config_path = os.path.join(os.path.dirname(__file__), 'api.ini')
        config.read(config_path)
        # print(f"perplexity Config file path: {config_path}")
        # print(f"perplexity Config sections: {config.sections()}")
        try:
            self.api_key = config['perplexity']['ACCESS_TOKEN']
        except KeyError as e:
            print(f"Error: Section/key not found in api.ini: {e}")
            print(f"Available sections: {config.sections()}")
            raise

    def search(self, query, force_refresh=False):
        """
        调用Perplexity API并缓存结果
        :param query: 搜索关键词
        :param force_refresh: 是否强制刷新缓存
        :return: API响应结果
        """
        cache_key = self._generate_cache_key(query)

        # 如果缓存中存在结果且不强制刷新，直接返回缓存结果
        if not force_refresh:
            cached_data = self._load_cache(cache_key)
            if cached_data is not None:
                # 如果缓存已经是字符串形式，直接返回
                if isinstance(cached_data, str):
                    return cached_data
                # 如果缓存是对象形式，转换为JSON字符串
                else:
                    return json.dumps(cached_data, ensure_ascii=False)

        # 调用Perplexity API
        print("调用Perplexity API搜索...")
        url = "https://api.perplexity.ai/chat/completions"
        
        payload = {
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": "Be precise and concise."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "max_tokens": 6000,
            "temperature": 0.2,
            "top_p": 0.9,
            "search_domain_filter": None,
            "return_images": False,
            "return_related_questions": False,
            "search_recency_filter": "year",  # Set to a valid value or remove this line if not needed
            "top_k": 0,
            "stream": False,
            "presence_penalty": 0,
            "frequency_penalty": 1,
            "response_format": None
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.request("POST", url, json=payload, headers=headers)
            response.raise_for_status()  # 抛出异常如果请求失败
            
            if response.status_code == 200:
                # json string
                result = response.text
                # 保存到缓存
                self._save_cache(cache_key, result)
                return result
        except Exception as e:
            error_result = {
                "status": "error",
                "message": str(e),
                "query": query
            }
            return json.dumps(error_result, ensure_ascii=False)
    # 扩展功能，只针对Perplexity API 响应结果进行解析
    @staticmethod
    def extract_json_data(json_string):

        try:
            
            data = json.loads(json_string) if isinstance(json_string, str) else json_string
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
    @staticmethod
    def extract_json_from_content(text):
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
    @staticmethod
    # markdown table format
    def write_to_database(text):
        # 替换 \n\n 为两个空行，段落更清晰
        if text:
            text = text.replace("\\n\\n", "\n\n")
            # 替换 \n 为实际换行
            text = text.replace("\\n", "\n")
        return text


class GoogleSearch(BaseSearchWithCache):
    """使用Google Custom Search API进行搜索"""
    
    def __init__(self, cache_path='./Google_cached'):
        """
        初始化Google搜索类
        :param cache_path: 缓存文件路径
        """
        super().__init__(cache_path)
        # 读取配置文件
        config = configparser.ConfigParser()
        config.read('api.ini')
        self.api_key = config['google']['API_KEY']
        self.cse_id = config['google']['CSE_ID']

    def search(self, query, force_refresh=False, total_results=10, num=10, **kwargs):
        """
        搜索Google并缓存结果，支持分页查询
        :param query: 搜索关键词
        :param force_refresh: 是否强制刷新缓存
        :param total_results: 总共需要返回的条目数（默认30）
        :param num: 每次查询返回的条目数（默认10，最大100）
        :param kwargs: 其他搜索参数
        :return: 搜索结果
        """
        all_items = []
        start = 1  # 查询的起始位置

        while len(all_items) < total_results:
            cache_key = self._generate_cache_key(f"{query}_start{start}_num{num}")

            # 如果缓存中存在结果且不强制刷新，直接使用缓存结果
            if not force_refresh:
                cached_data = self._load_cache(cache_key)
                if cached_data is not None:
                    # 如果缓存是字符串形式，转换为列表
                    if isinstance(cached_data, str):
                        items = json.loads(cached_data)
                    # 如果缓存是对象形式，直接使用
                    else:
                        items = cached_data
                    all_items.extend(items)
                    start += num
                    continue

            # 调用Google Custom Search API
            print(f"调用Google Custom Search API搜索，起始位置：{start}，条目数：{num}...")
            try:
                service = build("customsearch", "v1", developerKey=self.api_key)
                res = service.cse().list(q=query, cx=self.cse_id, num=num, start=start, **kwargs).execute()
                items = res.get('items', [])
                
                # 转换为JSON字符串并保存到缓存
                json_result = json.dumps(items, ensure_ascii=False)
                self._save_cache(cache_key, json_result)
                
                all_items.extend(items)
                start += num
            except Exception as e:
                error_result = {
                    "status": "error",
                    "message": str(e),
                    "query": query
                }
                return json.dumps(error_result, ensure_ascii=False)

        # 返回前total_results条结果
        return json.dumps(all_items[:total_results], ensure_ascii=False)




class SearchFactory:
    """搜索工厂类，用于创建不同的搜索实例"""
    
    @staticmethod
    def get_searcher(search_method="perplexity"):
        """
        获取指定的搜索器实例
        
        :param search_method: 搜索方法，可选 "bocha" 或 "perplexity"
        :return: 搜索器实例
        """
        if search_method.lower() == "bocha":
            return BochaSearch()
        elif search_method.lower() == "perplexity":
            return PerplexitySearch()
        elif search_method.lower() == "google":
            return GoogleSearch()
        elif search_method.lower() == "azure":
            return AzureSearch()
        else:
            raise ValueError(f"未知的搜索方法: {search_method}")


def perform_search(query, search_method="perplexity", force_refresh=False):
    """
    统一的搜索接口，根据指定的方法执行搜索
    
    :param query: 搜索关键词
    :param search_method: 搜索方法，可选 "bocha" 或 "perplexity"
    :param force_refresh: 是否强制刷新缓存
    :return: 搜索结果
    """
    try:
        searcher = SearchFactory.get_searcher(search_method)
        result = searcher.search(query, force_refresh)
        #直接返回json string 格式
        return result
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"搜索错误: {str(e)}",
            "query": query
        }
        return error_result


if __name__ == '__main__':
    # 测试Bocha搜索
    # print("测试Bocha搜索:")
    # bocha_result = perform_search("Abacavir", search_method="bocha")
    # print(json.dumps(bocha_result, ensure_ascii=False, indent=2))
    
    # 测试Perplexity搜索
    # print("\n测试Perplexity搜索:")
    # perplexity_result = perform_search("is Aciclovir explicit Genotoxicity toxicity yes/no/unknown?")
    # print(json.dumps(perplexity_result, ensure_ascii=False, indent=2))
    # 测试Google搜索
    # print("\n测试Google搜索:")

    # # 可设置total_results参数来获取更多结果
    # google_result = perform_search("Abacavir dailymed", search_method="google")
    # print(google_result)
    
    # 测试Azure搜索
    print("\n测试Azure搜索:")
    azure_result = perform_search("is Abacavir toxicity? give out info from different resources", search_method="azure")
    print(azure_result)
