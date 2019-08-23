import jieba_fast as jieba
import jieba_fast.analyse
import pandas as pd
import os


class Threshold_Value():
    def __init__(self):
        # 读取股票代码
        self.abs_path = os.path.join(os.getcwd(), 'file')
        self.stock_code = pd.read_csv(os.path.join(self.abs_path, 'stock_code.csv'))
        self.positive_dict = {}
        self.negative_dict = {}
        with open(os.path.join(self.abs_path, 'Result.txt'), 'r') as f:
            dics = f.readlines()
            self.positive_dict = eval(dics[1])
            self.negative_dict = eval(dics[2])

    def stopwordslist(self, filepath):  # 调用停用表
        stopwords = [line.strip() for line in open(filepath, 'r', encoding='utf-8').readlines()]
        return stopwords

    def get_name(self, sentence):  # 获取sentence中的公司名字
        # 加载公司字典
        jieba.load_userdict(os.path.join(self.abs_path, 'company_list.txt'))

        sentence_seged = jieba.cut(sentence.strip(), cut_all=False)  # 不进行完全分割,公司名字粒度相对较大
        stopwords = self.stopwordslist(os.path.join(self.abs_path, "HIT_STOP.txt"))
        com_name = ''  # 公司名字
        for word in sentence_seged:
            if word not in stopwords:
                if word != '\t':
                    com_name = com_name + word + ' '
        com_name = jieba_fast.analyse.extract_tags(com_name, topK=1, withWeight=False, allowPOS=('x'))  # 过滤词性
        return com_name[0] if len(com_name) > 0 else ' '# 返回公司名

    def search_code(self, name):
        for index in range(len(self.stock_code)):
            if self.stock_code.iloc[index]['name'] == name:
                if index < 3663:
                    return str(self.stock_code.iloc[index]['symbol']).rjust(6, '0')
                elif 3663 <= index <= 6088:
                    return str(self.stock_code.iloc[index]['symbol']).rjust(5, '0')
                else:
                    return self.stock_code.iloc[index]['symbol']
        else:
            return ' '

    def threshold_value(self, sentence):
        """
        :param sentence: 待输入的新闻
        :return:列表各项分别代表积极/消极,公司名,公司股票代码,给出的概率
        """
        com_name = self.get_name(sentence)
        com_code = self.search_code(com_name)

        li = jieba.lcut(sentence, cut_all= True)

        p_threshold_value = 0
        n_threshold_value = 0

        for item in li:
            for key, value in self.positive_dict.items():
                if item == key:
                    p_threshold_value += value[4]
            for key, value in self.negative_dict.items():
                if item == key:
                    n_threshold_value += value[4]

        # print(com_name, com_code, p_threshold_value, n_threshold_value)

        if (p_threshold_value != 0 or n_threshold_value != 0) and com_name != ' ' and com_code != ' ' \
                and max(p_threshold_value, n_threshold_value) < 1.0:
            if p_threshold_value >= n_threshold_value:
                return ['positive', com_name, com_code, p_threshold_value]
            else:
                return ['negative', com_name, com_code, n_threshold_value]
        else:
            return []


if __name__ == '__main__':
    """
    示例
    """
    TV = Threshold_Value()
    s = '【东阿阿胶：上半年实现净利润1.9亿元 同比降77.62%】东阿阿胶(000423)8月21日晚披露半年报，公司实现营收18.9亿元，同比下滑36.69%；净利润1.93亿元，同比下滑77.62%；基本每股收益0.35元。股东名单方面，前海人寿再度现身公司十大股东名单，持股比例3.09%，此前，前海人寿-海利丰年曾于2016年一季报跻身公司十大股东名单，但于2016年年报中退出。（e公司）'
    l = TV.threshold_value(s)
    print(l)
