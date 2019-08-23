"""计算不同因素的权重"""

from Weight import Weight
import os


def dir_name(dirname):
    for root, dirs, files in os.walk(dirname):
        models = [file for file in files if 'model' == file[-5:]]
        return models


if __name__ == '__main__':
    d_name = os.path.join(os.getcwd(),'Main')
    models = dir_name(d_name)

    TI = Weight('news.csv', 'positive.txt', 'negative.txt', models)
    TI.run()

