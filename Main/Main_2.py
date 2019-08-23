"""对已获取的新闻进行分类"""
from code.Classification import Text_Classification
import os

if __name__ == '__main__':
    print('Main_Two')
    TC = Text_Classification()
    API_KEY, SECRET_KEY = 'xxx', 'xxx'
    TC.get_access_token('mOY4VgQffhYxFcLOeFTOilAC', '5DmVUsm97peqR7kWK694AHZpwHRUqaAG')

    Abs_Path = os.getcwd() + 'data'
    File_In = os.path.join(Abs_Path, 'news.csv')
    File_Out = os.path.join(Abs_Path, 'news_tagged.csv')
    TC.tag_document(File_In, File_Out)


