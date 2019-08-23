import asyncio
import os
import time

import aiohttp
import aiohttp.client_exceptions
from lxml import etree
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait


class Run_page:
    "翻页爬取新浪财经国内新闻并用协程爬虫对获取的url爬取相关的新闻"
    def __init__(self, url):
        self.options = self.set_options()
        self.driver = webdriver.Chrome(options=self.options)
        self.wait = WebDriverWait(self.driver, 10)
        self.url = url

    def set_options(self):
        options = Options()
        options.add_argument('Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A334 Safari/7534.48.3')
        # 手机端,用电脑端爬不到
        options.add_argument('--headless')
        # 无界面模式
        return options

    async def get(self, url1):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}
        try:
            session = aiohttp.ClientSession()
            response = await session.get(url1, headers=headers)
            # print(response.encoding)
            result = await response.text(encoding='utf-8', errors='ignore')
            await session.close()
            return result
        except asyncio.TimeoutError as e:
            print(e)
        except aiohttp.client_exceptions.ServerDisconnectedError as e:
            print(e)
        except aiohttp.client_exceptions.InvalidURL as e:
            print(e)
        except aiohttp.client_exceptions.ClientConnectorError as e:
            print(e)

    async def request(self, url1, save_id=0):
        print('Waiting for', url1)
        result = await self.get(url1)
        html = etree.HTML(result)   # 解析网址源码
        contents = html.xpath("//div[@id='artibody']//p/text()")  # 获取内容p标签
        content = ''
        title = ''
        for pos, line in enumerate(contents):  # contents为列表类型
            if pos == 0:
                title = line  # contents第一项为标题
            else:
                content += line
        title = title.replace('\u3000', '')
        content = content.replace('\u3000', '')
        content = content[0: content.find('责任编辑')]
        # print('Get response from', url1, 'Result:', content, '\n')
        with open('domestic_news.csv', 'a') as f:
            f.write(str(save_id) + ',' + '财经,' + title + ',' + content + '\n')

    def push_button(self, outpath):
        self.driver.get(self.url)
        time.sleep(2)
        page = 1
        while True:
            try:
                if page > 17100:  # 使用提前测试出的页数
                    break
                self.driver.execute_script("var q=document.documentElement.scrollTop=500")  # 移动到页面中部
                time.sleep(0.5)
                html = self.driver.page_source  # 得到网页源码
                htmls = etree.HTML(html)
                urls = htmls.xpath('//h2//a/@href')  # @href属性下的url
                print(page)  # 打印页数
                page += 1
                for url in urls:
                    print(url)
                    with open(outpath, 'a') as fin:  # 保存url
                            fin.write(url + '\n')
                time.sleep(0.05)
                self.driver.execute_script("var q=document.documentElement.scrollTop=3000")  # 移动到页面底部
                time.sleep(0.05)
                self.driver.find_element_by_class_name('pagebox_next').click()
            except Exception as e:
                print(e)

        # self.fetch_data()
        self.driver.quit()

    def fetch_data(self):
        with open('domestic_news.csv', 'a') as f:  # 后续的并发爬虫无序，所以提前创建csv文件并写入首行
            f.write('id,classification,title,content' + '\n')
        tasks = []
        with open('url_domestic1.txt', 'r') as fin:  # 保存url并且添加任务
            for save_id, url in enumerate(fin):
                # print(url)
                tasks.append(asyncio.ensure_future(self.request(url.replace('\n',''), save_id)))
                if (save_id+1) % 300 == 0:
                    start = time.time()
                    loop = asyncio.get_event_loop()
                    loop.run_until_complete(asyncio.wait(tasks))
                    tasks.clear()
                    time.sleep(3)
                    # loop.close()  # 关闭事件循环
                    end = time.time()
                    print('Cost time:', end - start)
                    print(save_id,'\n\n\n\n\n')



if __name__ == '__main__':
    url = 'http://finance.sina.com.cn/china/'
    pa = Run_page(url)
    pa.push_button('news_domestic.txt')
    pa.fetch_data()


