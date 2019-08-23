import os
import re
import asyncio
import aiohttp
import aiohttp.client_exceptions
from lxml import etree
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait


class Url_Fetch():
    def __init__(self):
        self.abs_path = os.path.join(os.getcwd(), 'data')

        self.options = self.set_options()
        self.driver = webdriver.Chrome(options=self.options)
        self.wait = WebDriverWait(self.driver, 10)
        self.url = 'https://news.sina.com.cn/roll/#pageid=153&lid=2516&k=&num=50&page=1'
        self.total_pages = self.final_page()  # 总页数

    def set_options(self):
        options = Options()
        options.add_argument('Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A334 Safari/7534.48.3')
        # 手机端,用电脑端爬不到
        options.add_argument('--headless')
        # 无界面模式
        return options

    def final_page(self):
        self.driver.get(self.url)
        self.driver.execute_script("var q=document.documentElement.scrollTop=3000")  # 移动到页面底部
        pages = self.driver.find_element_by_xpath('//*[@id="d_list"]/div/span[14]').text
        self.driver.quit()
        return int(pages)

    def save_url(self, url_content):
        with open(os.path.join(self.abs_path, 'roll_news_urls.txt'), 'a') as f:
            f.write(url_content + '\n')

    async def get_text(self, url1):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}
        try:
            session = aiohttp.ClientSession()
            response = await session.get(url1, headers=headers)
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

    async def request_url(self, url1):
        print('Waiting for', url1)
        rep = await self.get_text(url1)

        pat = re.compile(r'"wapurl".*?html')
        re1 = pat.findall(rep)
        for url_content in re1:
            # 清洗数据,获取url
            url_content = url_content.replace(r'\/', '/').replace('"wapurl":"', '')
            # 保存url
            self.save_url(url_content)

    def fetch_url(self):
        try:
            tasks = []
            loop = asyncio.get_event_loop()
            for page in range(1, self.total_pages):
                url = 'https://feed.mix.sina.com.cn/api/roll/get_text?pageid=153&lid=2516&k=&num=50&' + 'page=' + \
                      str(page) + '&r=0.2531454788743699&callback=jQuery1112041674159083866325_1562560191072&_=1562560191080'

                tasks.append(asyncio.ensure_future(self.request_url(url.replace('\n', ''))))
                loop.run_until_complete(asyncio.wait(tasks))
        except Exception as e:
            print(e)


class News_fetch():
    def __init__(self):
        self.abs_path = os.path.join(os.getcwd(), 'file')

    async def get_text(self, url1):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}
        try:
            session = aiohttp.ClientSession()
            response = await session.get(url1, headers=headers)
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

    async def request_text(self, url1, save_id):
        print('Waiting for', save_id)
        result = await self.get_text(url1)
        html = etree.HTML(result)
        contents = html.xpath("//section//p[@class='art_p']/text()")
        content = ''
        title = ''
        for pos, line in enumerate(contents):  # contents为列表类型
            if pos == 0:
                title = line  # contents第一项为标题
            else:
                content += line
        title = title.replace('\n', '')
        content = content[0: content.find('责任编辑')]
        content = content.replace('\n', '')

        # 写入内容
        with open(os.path.join(self.abs_path, 'news.csv', 'a')) as f:
            f.write(str(save_id) + ',' + '财经,' + title + ',' + content + '\n')

    def fetch_data(self):
        with open('news.csv', 'a') as f:  # 后续的并发爬虫无序，所以提前创建csv文件并写入首行
            f.write('id,classification,title,content' + '\n')
        tasks = []
        with open(os.path.join(self.abs_path, 'roll_news_urls.txt'), 'r') as fin:  # 保存url并且添加任务
            for save_id, url in enumerate(fin):
                tasks.append(asyncio.ensure_future(self.request_text(url.replace('\n', ''), save_id)))
                if (save_id + 1) % 10 == 0:
                    loop = asyncio.get_event_loop()
                    loop.run_until_complete(asyncio.wait(tasks))
                    tasks.clear()
                    print(save_id, '\n' * 5)



