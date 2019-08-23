"""利用百度api给分本分类"""
import json
import pandas as pd
import urllib
import urllib.request
import time
import os


class Text_Classification():
    def __init__(self):
        self.abs_path = os.path.join(os.getcwd(), 'data')

        self.access_token = ''

    def get_access_token(self, API_KEY, SECRET_KEY):
        """
        function:获取百度AI平台的Access Token
        """
        API_KEY = API_KEY
        SECRET_KEY = SECRET_KEY
        host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id='\
               +API_KEY+'&client_secret=' + SECRET_KEY
        request = urllib.request.Request(host)
        request.add_header('Content-Type', 'application/json; charset=UTF-8')
        response = urllib.request.urlopen(request)
        content = response.read().decode('utf-8')
        result = json.loads(content)
        self.access_token = result["access_token"]

    def add_list(self, filename_in, list_of_name, add_name):
        """
        :function: 向csv文件中添加一列
        :param filename_in:输入文件名  :param filename_out:输出文件名
        :param add_name:所要添加的列名,需要包括在list_of_name中
        """
        df = pd.read_csv(filename_in)
        df_add = pd.DataFrame(columns=[add_name])
        df = pd.concat([df_add, df],  axis=1)
        df = df[list_of_name]  # list_of_name可以设置保存顺序
        df.to_csv(filename_in)

    def get_tag(self, title, content):
        """
        :param title:文章标题
        :param content: 文章内容
        :return: 文章分类
        """
        token = self.access_token
        host = 'https://aip.baidubce.com/rpc/2.0/nlp/v1/topic?charset=UTF-8&access_token=' + token
        # 拼接出请求头
        # 需要在host中加上?charset=UTF-8，官方文档：
        # UTF-8支持：若文本需要使用UTF-8编码，请在url参数中添加charset=UTF-8 （大小写敏感）
        body = {'title': str(title), 'content': str(content)}
        request = urllib.request.Request(url=host, data=json.dumps(body).encode('utf-8'))
        request.add_header('Content-Type', 'application/json')  # 添加请求头,官网文档要求
        response = urllib.request.urlopen(request, timeout=60)  # 设置连接超时时间为60s
        content = response.read().decode('utf-8')

        return json.loads(content)

    def tag_document(self, filename_in, filename_out):
        """
        :function 利用百度API为csv文件文本添加标签
        :param filename_in: 输入文件名
        :param filename_out: 输出文件名
        :param access_token: 百度api的access_token
        """

        df = pd.read_csv(filename_in, error_bad_lines=False, engine='python')
        df.fillna('0')  # 填充nan
        df = df[pd.notnull(df['content'])]  # 去除content为空的行
        # 逐行遍历df
        flag = 0  # 控制保存时第一个保存值需要保存列名
        for pos, index in enumerate(range(0, len(df))):
            time.sleep(0.2)  # 控制访问接口的流量
            content = df.iloc[index]['content']
            title = str(df.iloc[index]['title'])[0:30]  # 限制输入长度
            try:

                class_tag = self.get_tag(title, content)
                tag_1 = class_tag.get_text('item', 'item').get_text('lv1_tag_list', 'lv1_tag_list')
                if len(tag_1) == 0:
                    demo = df.iloc[index].copy()
                    demo['classification'] = '财经'
                    demo = demo.to_dict()
                    demo = pd.DataFrame(demo, index=[0])
                else:
                    print(pos, tag_1[0]['tag'])
                    demo = df.iloc[index].copy()
                    demo['classification'] = tag_1[0]['tag']
                    demo = demo.to_dict()
                    demo = pd.DataFrame(demo, index=[0])

                if flag == 0:
                    flag = 1
                    demo.to_csv(filename_out, mode='a', index=False)
                else:
                    demo.to_csv(filename_out, mode='a', index=False, header=0)

            except urllib.request.URLError as e:
                # 连接出错
                print(e.reason)
            except AttributeError as e:
                # 出现调用接口失败的情况,导致获取了错误信息
                print(e)
                demo = df.iloc[index].copy()
                demo['classification'] = '财经'
                demo = demo.to_dict()
                demo = pd.DataFrame(demo, index=[0])
                demo.to_csv(filename_out, mode='a', index=False, header=0)
            except ConnectionResetError as e:
                print(e)
            except Exception as e:
                print(e)

