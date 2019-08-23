from math import log2
import pandas as pd
from gensim.models import Doc2Vec
import json
from math import log1p
import os


class Weight():
    def __init__(self, csv_file, pos_ele_file, neg_ele_file, model_file):
        """
        :param csv_file:已经分词的csv文件
        :param pos_ele_file: 积极因素文本文件
        :param neg_ele_file: 消极因素文本文件
        :param model_file: 模型路径列表
        """
        self.abs_path = os.path.join(os.getcwd(), 'file')

        self.csv_file = os.path.join(self.abs_path, csv_file)
        self.df = self.read_csv(self.csv_file)

        self.sum_dic = {}  # 存储词数和文档数

        self.arg_dic = {'arg': 0}  # 存储参数,计算不同参数下的数据方差

        self.pos_ele_list = []  # 存储积极因素
        self.neg_ele_list = []  # 存储消极因素

        self.pos_ti_dic = {}  # 存储积极结果
        self.neg_ti_dic = {}  # 存储消极结果

        self.pos_ele_file = os.path.join(self.abs_path, pos_ele_file)
        self.neg_ele_file = os.path.join(self.abs_path,neg_ele_file)

        self.models = []
        for file in model_file:
            file = os.path.join(os.path.join(os.getcwd(), 'model'), file)
            self.models.append(Doc2Vec.load(file))

    def read_csv(self, file):
        df = pd.read_csv(file, error_bad_lines=False, engine='python')
        df = df[pd.notnull(df['content'])]  # 去除content为空的行
        return df

    def read_element(self):
        with open(self.pos_ele_file, 'r') as p, open(self.neg_ele_file, 'r') as n:
            for line in p.readlines():
                if line:
                    self.pos_ele_list.append(line.replace('\n', ''))
            for line in n.readlines():
                if line:
                    self.neg_ele_list.append(line.replace('\n', ''))

    def sum_words(self):
        """计算总文档数以及总词数"""
        s_words, s_pages = 0, 0
        for pos, index in enumerate(range(0, len(self.df))):
            s_pages = pos
            content = self.df.iloc[index]['content']
            content = content.split(' ')
            s_words += len(content)
        self.sum_dic['s_words'] = s_words
        self.sum_dic['s_pages'] = s_pages

    def tf_idf(self, ele_list, ele_dic):
        """
        :param ele_list:因素列表
        :param ele_dic: 因素词典
        """
        for element in ele_list:
            ele_dic[element] = [0, 0, 0, 0, 0]  # 五个维度分别代表tf，idf，tf*idf，相似度，模型修正值
        for pos, index in enumerate(range(0, len(self.df))):
            content = self.df.iloc[index]['content']
            for element in ele_list:
                if element in content:
                    count = content.count(element)
                    ele_dic[element][0] += count
                    ele_dic[element][1] += 1

        s_words = self.sum_dic['s_words']
        s_pages = self.sum_dic['s_pages']
        for element in ele_list:
            tf = ele_dic[element][0] / s_words
            idf = log2(s_pages / (ele_dic[element][1] + 1))
            ele_dic[element][2] = tf * idf

    def save_dic(self, dic):
        with open('Result.txt', 'a') as f:
            json.dump(dic, f, ensure_ascii=False)
            f.write('\n')

    def model_correct(self, corr_word, ele_dic):  # 传入修正词
        """
        修正方法：log1p( tf-idf权重值(0-1之间,权重越高值越接近1) / ( 1 -  模型相似度（0-1之间,权重越高值越接近1）)  + 0.1(修正值) )
        """
        sum = 0
        for key, value in ele_dic.items():
            sum += value[2]
            print(key, value[2])

        for key, value in ele_dic.items():
            try:
                sim = value[2] / sum  # tf-idf 权重值
                value[2] = float(sim)  # 更新tf-idf（第一次修正）
                sim1 = 0
                for model in self.models:
                    sim1 += model.wv.similarity(corr_word, key)
                sim1 /= len(self.models)

                value[3] = float(sim1)  # 相似度

                arg = 1.0
                self.arg_dic['arg'] = arg
                value[4] = float(log1p(sim / (arg-sim1) + 0.1))
            except Exception as e:
                print(e)

        # sum_1 = 0
        # for key, value in ele_dic.items():
        #     sum_1 += value[4]
        #
        # for key, value in ele_dic.items():
        #     value[4] = value[4] / sum_1

        print('\n\n-----------weight---------\n\n')
        for key, value in ele_dic.items():
            print(key, 'similarity=', value[3], 'threshold_value=', value[4])  # 第二次修正

    def model_correct1(self, corr_word, ele_dic):  # 传入修正词
        """
        修正方法：log1p( 模型相似度（0-1之间,权重越高值越接近1  ** tf-idf权重值(0-1之间,权重越高值越接近1) )
        偏差较大
        """
        sum = 0
        tmp = []
        for key, value in ele_dic.items():
            sum += value[2]
            print(key, value[2])

        for key, value in ele_dic.items():
            try:
                sim = value[2] / sum  # tf-idf 权重值
                value[2] = float(sim)  # 更新tf-idf（第一次修正）
                sim1 = 0
                for model in self.models:
                    sim1 += model.wv.similarity(corr_word, key)
                sim1 /= len(self.models)

                value[3] = float(sim1)

                tmp.append(float(log1p(sim1 ** sim)))
                value[4] = float(log1p(sim1 ** sim))
            except Exception as e:
                print(e)

        print('\n\n-----------weight---------\n\n')
        for key, value in ele_dic.items():
            print(key, 'similarity=', value[3], 'threshold_value=', value[4])  # 第二次修正

    def run(self):
        self.read_element()

        # 获取并保存总词数和文档数
        self.sum_words()
        self.save_dic(self.sum_dic)

        self.tf_idf(self.pos_ele_list, self.pos_ti_dic)
        self.model_correct('上涨', self.pos_ti_dic)
        # 保存积极词典
        self.save_dic(self.pos_ti_dic)

        self.tf_idf(self.neg_ele_list, self.neg_ti_dic)
        self.model_correct('下跌', self.neg_ti_dic)
        # 保存消极词典
        self.save_dic(self.neg_ti_dic)

        # 保存参数字典
        self.save_dic(self.arg_dic)


