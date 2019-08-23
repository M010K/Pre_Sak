"""
准备训练数据
"""
from code.News import Url_Fetch
from code.News import News_fetch

if __name__ == '__main__':
    print('Main_One')
    # 获取新闻url
    RNF = Url_Fetch()
    RNF.fetch_url()

    # 爬取新闻
    NF = News_fetch()
    NF.fetch_data()


