# ToxiClassify Version 1.0
import os
import re
import sys
import json
import requests
import time
import random
import string
import shutil
from urllib.parse import urlparse
from argparse import ArgumentParser
from openai import OpenAI
import configparser


# 返回数据类型为dict
class AITEP:

    def __init__(self, api_key=None, base_url=None, debug=True):
        """
        初始化AITEP类
        :param api_key: OpenAI API Key
        :param base_url: OpenAI Base URL
        :param debug: 是否开启调试模式
        """
        if not api_key:
            config = configparser.ConfigParser()
            # 获取当前文件所在目录的路径
            config_path = os.path.join(os.path.dirname(__file__), 'api.ini')
            config.read(config_path)
            # print(f"Config file path: {config_path}")
            # print(f"Config sections: {config.sections()}")
            try:
                api_key = config['TongYiQianWen']['ACCESS_TOKEN']
            except KeyError as e:
                print(f"Error: Section/key not found in api.ini: {e}")
                print(f"Available sections: {config.sections()}")
                raise
        self.api_key = api_key
        if not base_url:
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.base_url = base_url
        self.debug = debug
        self.msg = None
        epoch_time_ms = int(time.time() * 1000)
        self.tmp_dir = "/tmp/aitep"
        if os.path.exists(self.tmp_dir) and os.path.isdir(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)
        self.output_dir = "{}/{}".format(self.tmp_dir, epoch_time_ms)
        os.makedirs(self.output_dir, exist_ok=True)
        self.max_tokens=6000

        # 读取传过来的参数data
        parser = ArgumentParser()
        parser.add_argument("-d", "--data", dest="data")
        if "ipykernel" in sys.modules:
            args = parser.parse_args(args=[])  # Avoid parsing notebook arguments
        else:
            args = parser.parse_args()  # Standard behavior for scripts

        # 默认的命令行输入参数
        self.params = {
            "url": "https://xanda.oss-cn-shenzhen.aliyuncs.com/aitep/2923395ca30814db31c780c3e775e2ca.pdf",
            "data": {"APID": "A00174", "drug_name": "Gentamicin", "route": "Topical", "id": 4},
        }
    
        if args and args.data:
            self.params = json.loads(args.data)

        self.file_name = "downloaded_file.pdf"
        self.pdf_file = os.path.join(self.output_dir, self.file_name)  # 本地保存的文件名
        self.output_file = os.path.join(self.output_dir, f"{os.path.splitext(self.file_name)[0]}.json") # 输出的JSON文件名
        self.file_id=None

    def init_llm(self):
        # 根据模型的名称进行初始化
        self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url)
       

    def output(self, data={}):
        # 输出结果到Stdout
        print("````JSON")
        print(json.dumps(data, indent=4, ensure_ascii=False))
        print("````")

    def output_to_stdout(self,result=[],file=None,file_type='json'):
        if file is None and self.output_file:
            file=self.output_file
        if file:
            if self.save_json_to_local(result,file):
                data={
                    'file':file,
                    'file_type': file_type,
                    'msg': self.msg
                }
                self.output(data)
        else:
            print("Param file can't be empty")

    @staticmethod
    def combine_results(r1,r2):
        d1=r1.get('data')
        d2=r2.get('data')
        d=d1+d2
        u1=r1.get('usage')
        u2=r2.get('usage')
        u={
            'completion_tokens':u1['completion_tokens']+u2['completion_tokens'],
            'prompt_tokens':u1['prompt_tokens']+u2['prompt_tokens'],
            'total_tokens':u1['total_tokens']+u2['total_tokens']
        }
        return {'data':d,'usage':u}
    
    def post_json(self, url, data={}):
        # POST数据到url
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            content_type = response.headers.get('Content-Type')
            if "json" in content_type:
                return response.json()
            elif "text" in content_type:
                return response.text
            else:
                return response.content
        except requests.exceptions.HTTPError as err:
            self.msg = f"post_json error occurred: {err}"
            if self.debug:
                print(self.msg)
            return None

    def get_json(self, url):
        # GET json格式的数据
        try:
            response = requests.get(url)
            response.raise_for_status()

            content_type = response.headers.get('Content-Type')
            if "json" in content_type:
                return response.json()
            else:
                self.msg = f"Unexpected content type: {content_type}. returned maybe not JSON"
                if self.debug:
                    print(self.msg)
                return None

        except requests.exceptions.HTTPError as err:
            self.msg = f"get_json error occurred: {err}"
            if self.debug:
                print(self.msg)
            return None

    def get_file(self, url, outfile=None, retries=3):
        # GET下载文件, outfile 设定值将文件保存到这个路径，否则返回文件的binary
        if (not outfile) and self.pdf_file:
            outfile=self.pdf_file
        if not outfile:
            parsed_url = urlparse(url)
            file_name = os.path.basename(parsed_url.path)
            outfile = "{}/{}".format(self.output_dir, file_name)
        attempt = 0
        while attempt < retries:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
                response = requests.get(url, headers=headers, stream=False)
                response.raise_for_status()
                content = response.content
                if outfile:
                    with open(outfile, 'wb') as f:
                        f.write(content)
                    return outfile
                else:
                    return content
            except requests.exceptions.RequestException as e:
                if self.debug:
                    print(f"Error downloading file (attempt {attempt + 1}): {str(e)}")
                attempt += 1
                time.sleep(2)  # Wait before retrying

        self.msg = f"Failed to download file after {retries} attempts."
        if self.debug:
            print(self.msg)
        if outfile and os.path.exists(outfile):
            os.remove(outfile)
        return None

    def save_json_to_local(self,json_data,outfile):
        print("Output JSON:\n\n",json.dumps(json_data,indent=4),"\n")
        with open(outfile, 'w') as f:
            f.write(json.dumps(json_data, ensure_ascii=False))
        if os.path.exists(outfile):
            return True
        else:
            print("Outfile ({}) not exist".format(outfile))
            return False

    def chat_with_llm(self, llm_model='qwen-long', prompt="你是谁"):
        try:
            messages = [
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': prompt}
            ]

            # Use non-streaming version of chat completion to simplify handling
            completion = self.client.chat.completions.create(
                model=llm_model,
                messages=messages,
                stream=False
            )
            res = completion.model_dump_json()
            res = json.loads(res)

            if res and 'choices' in res:
                result = res['choices'][0]['message']['content']
                return result
            else:
                print(res)
                return None
        except Exception as e:
            self.msg = f"chat_with_llm error: {str(e)}"
            if self.debug:
                print(self.msg)
        return None

    def extract_json_from_llm_output(self, res):
        # 提取最后输出的json
        pattern = r'```json(.+?)```'
        matches = re.findall(pattern, res, re.DOTALL)
        count=len(matches)
        data = []
        if count>0:
            json_data = matches[-1].strip()
            #print('json_data',json_data)
            if self.is_json(json_data):
                data=json.loads(json_data)
            else:
                # 提取数组中前面几个完整的结构{}
                data=self.extract_valid_sections(json_data)
        else:
            self.msg = "\nNo JSON found in LLM_output\n"
            print(self.msg)
        return data

    def extract_valid_sections(self,output):
        newOutput=[]
        pattern=r'({.+?})'
        match=re.findall(pattern,output,re.DOTALL)
        #print('extract_valid_sections',match,output)
        for row in match:
            try:
                row1=self.format_json(row)
                if not self.is_json(row1):
                    if r'\*' in row1:
                        row1=row1.replace(r'\*','*')
                row2=json.loads(row1)
                newOutput.append(row2)
                #print(json.dumps(row2,indent=4))
            except json.JSONDecodeError:
                self.msg = "JSON parse error: " + row
                print("\n\n")
                print(self.msg)
        return newOutput

    def is_json(self,myjson):
        try:
            json.loads(myjson)
        except ValueError:
            return False
        return True
    
    def format_json(self,s):
        rows=s.splitlines()
        newS=''
        pattern1=r'.+"$|.+",$'
        pattern2=r'"references":.+]$'
        for row in rows:
            line=row.strip()
            # 替换错误的反转义
            #line=line.replace(r'\*','*')
            match1=re.search(pattern1,line)
            match2=re.search(pattern2,line)
            if line=='{' or line=='}' or match1 or match2:
                newS+=line
            else:
                newS+=line
        return newS

    def run_llm_with_multiple_sections(self, file_id=None, prompt=None,section_titles=[]):
        # 按固定格式提取PDF文档中的多个sections, 当completion_tokens超过6000时，自动将sections拆分，重新提取没有完成的sections
        # prompt 中必须包含 {{SECTIONTITLES}}
        # section_titles 为要提取的section的数组，每个元素是一个要提取的section标题
        # 为了防止陷入无限循环，section_titles会最多被拆分为3次
        """
        Extract sections from the uploaded PDF using OpenAI
        """

        if file_id is None and self.file_id:
            file_id=self.file_id
         
        newPrompt=prompt.replace('{{SECTIONTITLES}}',"\n".join(section_titles))

        print("\n\n======newPrompt======\n{}".format(newPrompt))
        
        r = self.run_llm(file_id, llm_model="qwen-long", prompt=newPrompt)
        section_len=len(section_titles)

        #print(r)

        runTimes=1
        while runTimes<4:
            data_len=len(r.get('data'))
            if data_len<section_len:
                print("Only {}/{} sections been extracted successfully after RUN {}".format(data_len,section_len,runTimes))
                subsection_titles=section_titles[data_len:]
                newPrompt=prompt.replace('{{SECTIONTITLES}}',"\n".join(subsection_titles))
                print("\n\n======newPrompt======\n{}".format(newPrompt))
                r1 = self.run_llm(file_id, llm_model="qwen-long", prompt=newPrompt)
                r=self.combine_results(r,r1)
                runTimes+=1
            else:
                break
        return r

    @staticmethod
    def rand_string():
        random_string = ''.join(random.choices(string.ascii_uppercase, k=5))
        return random_string
        
    def run_llm(self, file_id=None, llm_model='qwen-long', prompt=None,keywords=[]):
        # 根据大模型从PDF文件中提取信息
        # Prompt中不支持动态变量，获得JSON数据以后再处理
        # pdf_file为URL时，先下载到本地临时文件夹，然后再上传
        """
        Extract sections from the uploaded PDF using OpenAI
        """
        self.init_llm()
        if file_id is None and self.file_id:
            file_id=self.file_id
        data = []
        result = ""
        reasoning_content=""
        res = None
        usage = None
        try:
            # 替换敏感词
            mapping={}
            for keyword in keywords:
                rstring=self.rand_string()
                mapping[keyword]=rstring
                prompt = re.sub(keyword, rstring, prompt, flags=re.IGNORECASE)
            
            messages = [
                {'role': 'system', 'content': 'You are an expert at extracting structured information from PDE reports.'}
            ]
            if file_id:
                messages.append({'role': 'system', 'content': f'fileid://{file_id}'})
            messages.append({'role': 'user', 'content': prompt})

            # Use non-streaming version of chat completion to simplify handling
            completion = self.client.chat.completions.create(
                model=llm_model,
                extra_body={"enable_search": True},  # 控制是否启用互联网搜索
                messages=messages,
                stream=True,
                max_tokens=self.max_tokens,
                stream_options={"include_usage": True}
            )
            request_id=None
            for chunk in completion:
                res = json.loads(chunk.model_dump_json())
                
                if request_id is None:
                    request_id=res['id']
                    print("request id: {}\n\n==================LLM model ({}) Output Start==================\n".format(request_id,llm_model))
                choices = res['choices']
                if len(choices) > 0:
                    output=""
                    # print(choices[0])
                    if choices[0].get('delta').get('reasoning_content'):
                        output=choices[0]['delta']['reasoning_content']
                        if output:
                            reasoning_content += output
                    else:
                        output=choices[0]['delta']['content']
                        if output:
                            result += output
                    if output:
                        print(output, end="")
                else:
                    usage = res['usage']
            if self.debug:
                print("\n\n==================LLM model ({}) Output End==================".format(llm_model))
                print("\n==================Token Usage of ({})==================".format(llm_model))
                print(usage)
                print("")

            # 替换回敏感词
            for keyword in keywords:
                rstring=mapping.get(keyword)
                result=result.replace(rstring,keyword)
                result=re.sub(rstring,keyword, result, flags=re.IGNORECASE)
            data = self.extract_json_from_llm_output(result)
        except Exception as e:
            self.msg = f"Extract error: {str(e)}"
            if self.debug:
                print(self.msg)
                print(result)
                print(res)
        
        r={'data': data, 'usage': usage}
        if reasoning_content:
            r['reasoning_content']=reasoning_content
        return r

    def upload_to_openai(self, file=None):
        """
        Upload a local file to OpenAI
        """
        if file is None and self.pdf_file:
            file=self.pdf_file
        try:
            if self.debug:
                print("Uploading to openai: {}".format(file))
            if not os.path.exists(file):
                raise FileNotFoundError(f"File not found: {file}")

            # Use OpenAI SDK to upload the file
            with open(file, "rb") as f:
                file_object = self.client.files.create(
                    file=f,
                    purpose="file-extract"
                )
            if self.debug:
                print(f"Successfully uploaded file. File ID: {file_object.id}")
            self.file_id=file_object.id
            return self.file_id
        except Exception as e:
            self.msg = f"Error uploading to OpenAI: {str(e)}"
            if self.debug:
                print(self.msg)
            return None


if __name__ == "__main__":
    name="aspirin"
    # 实例化
    ai = AITEP()
    # 调用LL
    result=ai.run_llm(llm_model="qwen-plus", prompt="请搜索{}的基本信息 Chemical Name, Synonyms, CAS Number, Molecular Formula, Molecular Weight, SMILES, InChI, InChIKey,IUPAC Name".format(name))
