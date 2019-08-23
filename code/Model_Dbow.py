import jieba
import pandas as pd
from gensim.models import Doc2Vec
from gensim.models.doc2vec import TaggedDocument
from tqdm import tqdm
from sklearn import utils
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, recall_score
import numpy as np
import json
import pickle
import os


class Model_Dbow():
    def __init__(self, model_name, file_path, stop_file):
        """
        :param model_name: 保存model的名字
        :param file_path: csv文件的路径(文件中必须有content,classification两列)
        :param stop_file: 停用词表文件路径
        """
        self.abs_path = os.path.join(os.getcwd(), 'file')
        self.save_path = os.path.join(os.getcwd(), 'data')

        self.file_path = file_path
        self.stop_file = stop_file
        self.args_dic = {}
        self.precision_dic = {}
        self.model_name = model_name

    def Read_File(self):
        # 参数error_bad_lines=False 防止读取出现错误
        df = pd.read_csv(self.file_path, error_bad_lines=False, nrows=1000)  # skiprows=[10000], nrows=5000

        df = df[['content', 'classification']]
        df = df[pd.notnull(df['content'])]  # 去除content为空的行
        df['content'] = df['content'].apply(self.pre_seg)  # 训练时先使用已经分好词的数据

        return df

    @classmethod
    def is_num(cls, obj):
        """
        :param obj:传入需要判断对象
        :return: 返回对象是否为整数或浮点数
        """
        return isinstance(obj, int) or isinstance(obj, float)

    @classmethod
    def turn_to_list(cls, text):
        return str(text).split()

    def pre_seg(self, sentence):  # 预分词
        jieba.load_userdict(os.path.join(self.abs_path, 'THUOCL_caijing.txt'))
        sentence_seged = jieba.cut(sentence.strip(), cut_all=False)
        # 获取停用词表
        stopwords = [line.strip() for line in open(self.stop_file).readlines()]
        # 去除停用词以及数字
        words_nostop = [x for x in sentence_seged if (not self.is_num(x)) and (x not in stopwords)]
        return ' '.join(words_nostop)

    def vec_for_learning(self, model, tagged_docs):
        sents = tagged_docs.values
        targets, regressors = zip(*[(doc.tags[0], model.infer_vector(doc.words, steps=20)) for doc in sents])
        return targets, regressors

    def train_model_dbow(self, train_tagged):
        """
        :param train_tagged:分类后的训练集
        :return: dbow模型
        """
        num_features = 400  # 特征向量的维度
        min_word_count = 5  # 词频少于min_count次数的单词会被丢弃掉, 默认值为5,中文词粒度较大
        context = 10  # 表示当前词与预测词在一个句子中的最大距离是多少
        negative = 5  # 指定应该绘制多少个“噪声字”
        sample = 1e-5  # 用于配置哪些高频率单词是随机向下采样的阈值，官网给的解释 1e-5效果比较好
        alpha = 0.05
        min_alpha = 0.05
        model_dbow = Doc2Vec(vector_size=num_features,
                             min_count=min_word_count, window=context,
                             negative=negative, sample=sample,
                             alpha=alpha, min_alpha=min_alpha
                             )
        model_dbow.build_vocab([x for x in tqdm(train_tagged.values)])
        # 迭代10次
        # utils.shuffle的作用为随机置乱原有序列进行迭代,效果更好
        for epoch in range(30):
            model_dbow.train(utils.shuffle([x for x in tqdm(train_tagged.values)]), total_examples=len(train_tagged.values),
                             epochs=1)
            model_dbow.alpha -= 0.002
            model_dbow.min_alpha = model_dbow.alpha  # 每次降低学习速率

        # 保存模型与训练参数
        model_dbow.save(self.model_name)

        with open(os.path.join(self.save_path, 'Precision.txt'), 'a') as f:
            self.args_dic['vector_size'] = num_features
            self.args_dic['min_count'] = min_word_count
            self.args_dic['window'] = context
            self.args_dic['negative'] = negative
            self.args_dic['sample'] = sample
            self.args_dic['alpha'] = alpha; self.args_dic[min_alpha] = min_alpha
            json.dump(self.args_dic, f)

        return model_dbow

    def test_model_dbow(self, model_dbow, train_tagged, test_tagged):
        # 获取训练出的向量
        y_train, X_train = self.vec_for_learning(model_dbow, train_tagged)
        y_test, X_test = self.vec_for_learning(model_dbow, test_tagged)

        # 利用逻辑回归进行分析
        print("start logisticRegression")
        # logreg = LogisticRegression(C=1e5)
        logreg = LogisticRegression()
        logreg.fit(X_train, y_train)
        y_pred = logreg.predict(X_test)

        self.precision_dic['Accuracy'] = accuracy_score(y_test, y_pred)
        self.precision_dic['Recall_Score'] = recall_score(y_test, y_pred, average='micro', labels=np.unique(y_pred))
        self.precision_dic['F1_Score'] = f1_score(y_test, y_pred, average='micro', labels=np.unique(y_pred))

        print('Testing accuracy of model_dbow %s' % self.precision_dic['Accuracy'])  # 模型精度
        #  在预测数据中存在实际类别没有的标签,会报出warning
        print("Tseting recall score of model_dbow: %s" % self.precision_dic['Recall_Score'])  # 模型召回率
        print('Testing F1 score of model_dbow: %s' % self.precision_dic['F1_Score'])

        # 保存精度
        with open(os.path.join(self.save_path, 'Precision.txt'),'a') as f:
            json.dump(self.precision_dic, f)

    def run(self):
        # 数据读入
        df = self.Read_File()
        # 准备训练与测试数据 训练集占75% 测试集占30% 设置种子为0 便于后续调参
        train, test = train_test_split(df, random_state=0, test_size=0.25)
        train_tagged = train.apply(
            lambda r: TaggedDocument(words=self.turn_to_list(r['content']), tags=[r.classification]), axis=1)
        test_tagged = test.apply(
            lambda r: TaggedDocument(words=self.turn_to_list(r['content']), tags=[r.classification]), axis=1)

        # 保存训练集与测试集(以二进制方式保存)
        with open(os.path.join(self.save_path, 'Train_Tagged.pickle'), 'wb') as f, open(os.path.join(self.save_path, 'Test_Tagged.pickle'), 'wb') as t:
            pickle.dump(train_tagged, f)
            pickle.dump(test_tagged, t)

        # 训练模型
        model_dbow = self.train_model_dbow(train_tagged)
        # 测试模型
        self.test_model_dbow(model_dbow, train_tagged, test_tagged)




