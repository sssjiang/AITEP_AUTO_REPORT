# 1. Google Custom Search API（推荐）
# 这是 Google 官方提供的搜索 API，需要：
# 创建 Google Cloud Project
# 获取 API Key
# 创建自定义搜索引擎（CSE）
from googleapiclient.discovery import build
# 使用示例
from argparse import ArgumentParser
from openai import OpenAI
import configparser

# 读取配置文件
config = configparser.ConfigParser()
config.read('api.ini')
API_KEY = config['google']['API_KEY']
CSE_ID = config['google']['CSE_ID']
def google_search(query, **kwargs):
    api_key=API_KEY
    cse_id=CSE_ID
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=query, cx=cse_id, **kwargs).execute()
    return res['items']


if __name__ == "__main__":

    try:
        results = google_search('aciclovir Topical route dailymed')
        for result in results:
            print(result['title'])
            print(result['link'])
            print(result['snippet'])
            print('---')
    except Exception as e:
        print(f"Error: {e}")
