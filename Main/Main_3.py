"""训练模型"""
import os
from Model_Dbow import Model_Dbow


if __name__ == '__main__':


    model_name = input('请输入模型名字')
    Abs_Path = os.getcwd()
    File_In = os.path.join(Abs_Path + 'data', 'news_tagged.csv')
    File_Stop = os.path.join(Abs_Path + 'file', 'HIT_STOP.txt')

    MD = Model_Dbow(model_name, File_In, File_Stop)
    MD.run()

