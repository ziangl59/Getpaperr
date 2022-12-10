from random import choice
from requests import get
from selenium import webdriver
from time import time
from bs4 import BeautifulSoup
import pandas as pd
from selenium.webdriver.common.keys import Keys
import re
from os import mkdir, path


# 爬取网页获取 doi
def get_links(theme, page):
    start_time = time()
    code = 'gfsoso'                                     # 验证码
    if not path.exists("./papers"):                     # 后续可以改成以主题命名
        mkdir("./papers")
    info = pd.DataFrame({"文章名": "示例", "doi": "示例", "发表年份": "示例",
                         "引用数": "示例", "摘要": "示例", "作者": "示例", "文章链接": "示例"}, index=range(1))
    for i in range(page):
        links = []                                      # 存文章链接，从谷歌学术获取
        cites = []                                      # 存文章引用，从谷歌学术获取
        years = []                                      # 存发表年份，从谷歌学术获取
        abstracts = []                                  # 摘要，谷歌学术获取
        url = "https://xs.zidianzhan.net/scholar?start=" + str(i*10) + "&q=" + str(theme) + "&hl=zh-CN&as_sdt=0,5"
        chrome_options = webdriver.ChromeOptions()      # 设置selenium选项
        chrome_options.add_argument("--headless")       # 设置无界面模式
        chrome_options.add_argument('--disable-gpu')    # 禁用gpu防止报错
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        driver.implicitly_wait(3)                       # 隐式等待，最长等待3s执行下步程序
        driver.encoding = 'utf-8'
        # if_code(driver, code)
        print("\r正在爬取第 %i 页，请耐心等待" % (i+1))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        papers = soup.find_all('div', attrs={'class': "gs_r gs_or gs_scl"})
        for paper in papers:
            if re.search(r'[图书]', str(paper)):         # 判断是否是无效的图书链接，有点问题，但是能用
                continue
            links.append((re.findall(re.compile(r'href="(.*?)"'), str(paper.find('h3', attrs={'class': "gs_rt"}))))[0])  # 获取文章链接
            cites.append(int((re.findall(re.compile(r'<a href=.*?>被引用次数：(.*?)</a>'),
                                    str(paper.find('div', attrs={'class': "gs_ri"}).find('div', attrs={'class': 'gs_fl'}))))[0]))  # 获取引用次数
            years.append(int((re.findall(re.compile(r'(\d{4})'), str(paper.find('div', attrs={'class': "gs_a"}))))[0])) # 获取发表年份
            abs1 = str((list(paper.find('div', attrs={'class': "gs_rs"})))[0])
            abs2 = str((list(paper.find('div', attrs={'class': "gs_rs"})))[2]).strip()
            abstracts.append(abs1+abs2)
        dois, paper_names, authors = get_paper(links)
        data = {
            "文章名": pd.Series(paper_names),
            "doi": pd.Series(dois),
            "发表年份": pd.Series(years),
            "引用数": pd.Series(cites),
            "摘要": pd.Series(abstracts),
            "作者": pd.Series(authors),
            "文章链接": pd.Series(links)
        }
        info_ = pd.DataFrame(data)
        info = pd.concat([info, info_])
        print("\r第%i页爬取完毕" % (i+1))
    info.to_csv('./papers/主题：%s+%i篇.csv' % (theme, (len(info)-1)), encoding='utf_8_sig', index=False)
    end_time = time()
    print('爬取用时 %.3f s' % (end_time-start_time))


# 判断是否要输入验证码
def if_code(driver, code):
    if driver.find_element("name", "pagepwd"):
        driver.find_element("name", "pagepwd").send_keys([code, Keys.ENTER])


# 将获取的链接输入到scihub中下载原文, 可以尝试多线程
def get_paper(links):
    url = 'https://sci-hub.et-fine.com/'
    dois = []
    authors = []
    paper_names = []
    for link in links:
        chrome_options = webdriver.ChromeOptions()      # 设置selenium选项
        chrome_options.add_argument("--headless")       # 设置无界面模式
        chrome_options.add_argument('--disable-gpu')    # 禁用gpu防止报错
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        driver.encoding = 'utf-8'
        driver.find_element("name", "request").send_keys(link, Keys.ENTER)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        if not soup.find_all('div', attrs={'id': "menu"}):
            dois.append('oops, cant get it')
            authors.append('oops, cant get it')
            paper_names.append('oops, cant get it')
            continue
        papers = soup.find_all('div', attrs={'id': "menu"})
        for paper in papers:
            doi = str((list(paper.find('div', attrs={'id': "citation"})))[-1]).strip()
            doi = re.sub(r'doi:', '', doi)
            dois.append(doi)
            author = str((list(paper.find('div', attrs={'id': "citation"})))[0]).strip()
            authors.append(author)
            paper_name = str((list(paper.find('div', attrs={'id': "citation"}).find('i')))[0]).split()
            paper_name = ' '.join(paper_name)
            paper_name = re.sub(r'/', '', paper_name)
            paper_name = re.sub(r'<sub>', '', paper_name)
            paper_name = re.sub(r'<sup>', '', paper_name)
            paper_name = re.sub(r'\+', '', paper_name)
            paper_names.append(paper_name)
            download_link = str(list(re.findall(re.compile(r'<a href.*?location.href=\'(.*?)\''),
                                                str(paper.find('div', attrs={'id': "buttons"}))))[0]).strip()
            download_link = re.sub(r'\\', '', str(download_link))
            path = "./papers/" + str(paper_name) + '.pdf'
            headers = random_user_agent()               # 后续可以加入代理ip地址进行多线程操作
            resp = get(download_link, headers=headers)
            if resp.status_code == 200:                 # 200 状态码表示网站正常
                with open(path, 'wb') as fp:
                    fp.write(resp.content)
                    fp.close()


    return dois, paper_names, authors


# 获取随机头文件
def random_user_agent():
    USER_AGENT_LIST = [
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36",
        "Dalvik/1.6.0 (Linux; U; Android 4.2.1; 2013022 MIUI/JHACNBL30.0)",
        "Mozilla/5.0 (Linux; U; Android 4.4.2; zh-cn; HUAWEI MT7-TL00 Build/HuaweiMT7-TL00) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
        "AndroidDownloadManager",
        "Apache-HttpClient/UNAVAILABLE (java 1.4)",
        "Dalvik/1.6.0 (Linux; U; Android 4.3; SM-N7508V Build/JLS36C)",
        "Android50-AndroidPhone-8000-76-0-Statistics-wifi",
        "Dalvik/1.6.0 (Linux; U; Android 4.4.4; MI 3 MIUI/V7.2.1.0.KXCCNDA)",
        "Dalvik/1.6.0 (Linux; U; Android 4.4.2; Lenovo A3800-d Build/LenovoA3800-d)",
        "Lite 1.0 ( http://litesuits.com )",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET4.0C; .NET4.0E; .NET CLR 2.0.50727)",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 Safari/537.36 SE 2.X MetaSr 1.0",
        "Mozilla/5.0 (Linux; U; Android 4.1.1; zh-cn; HTC T528t Build/JRO03H) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30; 360browser(securitypay,securityinstalled); 360(android,uppayplugin); 360 Aphone Browser (2.0.4)",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
        "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
        "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
        "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
        "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
        "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
        "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5",
        "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
        "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; LBBROWSER)",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E; LBBROWSER)",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 LBBROWSER",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; QQBrowser/7.0.3698.400)",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; 360SE)",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)",
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1",
        "Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; zh-cn) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b13pre) Gecko/20110307 Firefox/4.0b13pre",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:16.0) Gecko/20100101 Firefox/16.0",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
        "Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10"
    ]
    headers = {'User-Agent': choice(USER_AGENT_LIST)}
    return headers
