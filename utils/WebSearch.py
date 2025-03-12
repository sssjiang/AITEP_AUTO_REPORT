import os
import json
import hashlib
import requests
import configparser
import json
class SearchWithCache:
    def __init__(self, cache_path='./cached'):
        """
        初始化搜索类
        :param cache_path: 缓存文件路径
        """
        # 读取配置文件
        config = configparser.ConfigParser()
        config.read('api.ini')
        self.api_key=config['Bocha']['ACCESS_TOKEN']
        self.cache_path = cache_path

    def _load_cache(self,key):
        """加载缓存文件"""
        file="{}/{}".format(self.cache_path,key)
        if os.path.exists(file):
            print("Cache Found: {}".format(key))
            with open(file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def _save_cache(self,key,data):
        """保存缓存到文件"""
        file="{}/{}".format(self.cache_path,key)
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
        搜索 Google 并缓存结果
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


        # 调用 Google Search API
        print("调用 API 搜索...")
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

if __name__ == '__main__':
    # 测试
    search = SearchWithCache()
    data = search.search("Abacavirc")
    print(data)