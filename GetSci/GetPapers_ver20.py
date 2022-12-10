import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
from time import time, sleep
from multiprocessing.dummy import Pool
import re
from random import choice
import requests


       # link, cite, year, abstract
info_all = []



# 生成所有的url地址,一遍后续多线程访问
def generate_urls(theme, page):
    urls = []
    baseurl = ['https://scholar.lanfanshu.cn/scholar?start=', "https://xs.zidianzhan.net/scholar?start=", "https://sc.panda321.com/scholar?start="]
    for i in range(page):
        urls.append(choice(baseurl) + str(i*10) + "&q=" + str(theme) + "&hl=zh-CN&as_sdt=0,5")
    return urls



# 多线程获取网页内容并返回
def get_pages(url):
    user_agent = random_user_agent()
    # proxy = random_ip()
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")                       # 设置无界面模式
    chrome_options.add_argument("--disable-gpu")                    # 禁用gpu加速
    chrome_options.add_argument("--user-agent=%s" % user_agent)     # 随机头
    # chrome_options.add_argument("--proxy-server" + proxy)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    sleep(5)
    driver.encoding = 'utf-8'
    soup = BeautifulSoup(driver.page_source, "html.parser")
    pages = soup.find_all('div', attrs={'class': "gs_r gs_or gs_scl"})
    return pages


# 筛选获得的网页文本，不需要多线程，优化找寻逻辑
def get_links(page):
    sleep(0.1)
    if not re.search(r'\[图书\]|\[引用\]', str(page)):       # 筛除图书
        info_1 = []
        find_link = re.compile(r'href="(.*?)"')
        page_link = page.find('h3', attrs={'class': "gs_rt"})
        link = (re.findall(find_link, str(page_link))[0])
        find_cite = re.compile(r'<a href=.*?>被引用次数：(.*?)</a>')
        page_cite = page.find('div', attrs={'class': "gs_ri"}).find('div', attrs={'class': 'gs_fl'})
        cite = int(re.findall(find_cite, str(page_cite))[0])
        find_year = re.compile(r'(\d{4})')
        page_year = page.find('div', attrs={'class': "gs_a"})
        year = int((re.findall(find_year, str(page_year)))[0])
        abst = page.find('div', attrs={'class': "gs_rs"})
        abs1 = str((list(abst))[0])
        abs2 = str((list(abst))[2]).strip()
        abstract = abs1+abs2
        info_1.append((link, cite, year, abstract))
        return info_1


# 获取原文
def get_papers(link, cite, year, abstract):
    sleep(0.1)
    name_link = []
    baseurl = ["https://sci-hub.et-fine.com/", 'https://sci-hub.wf/', 'https://sci-hub.ren/']
    url = choice(baseurl) + str(link)
    session = requests.session()
    resp = session.get(url, headers=random_user_agent(), allow_redirects=False)
    resp = BeautifulSoup(resp.text, 'lxml')
    if resp.find('div', attrs={'id': "menu"}):                                      # 判定scihub是否收录该论文
        resp_doi = resp.find('div', attrs={'id': "citation"})                       # 定位到 doi 所在的 element_tree
        doi = str((list(resp_doi))[-1]).strip()
        doi = re.sub(r'doi:', '', doi)
        resp_author = resp.find('div', attrs={'id': "citation"})                    # 定位到 author 所在的 element_tree
        author = str(((list(resp_author)))[0]).strip()
        author = re.compile(r'\(\d{4}\)').sub('', author)
        resp_name = resp.find('div', attrs={'id': "citation"}).find('i')            # 定位到 name 所在的 element_tree
        name = str((list(resp_name))[0]).strip()
        name = revise_name(name)
        resp_download_link = str(resp.find('div', attrs={'id': "buttons"}))         # 定位到 download_link 所在的 element_tree
        rule_download_link = re.compile(r'<a href.*?location.href=\'(.*?)\'')
        download_link = list(re.findall(rule_download_link, resp_download_link))[0]
        download_link = re.compile(r'\\').sub('', str(download_link).strip())
        # print(download_link)
        name_link.append((name, download_link))
    else:                                                                           # 没收录则添加未找到
        doi = 'oops, cant find it'
        author = 'oops, cant find it'
        name = 'oops, cant find it'
    info_all.append([name, cite, abstract, author, year, doi, link])
    return name_link
# 保存了作者，文章名，下载链接，doi


# 修改文章名
def revise_name(name):
    if re.search(r'.', name):
        name = name.split('.')
        name = name[0]
    else:
        name = name.split()
        name = ' '.join(name)
    name = re.compile(r'<sub>').sub('', name)
    name = re.compile(r'<sup>').sub('', name)
    name = re.compile(r'/').sub('', name)
    name = re.compile(r'\+').sub('', name)
    name= name.split()
    name = ' '.join(name)
    return name


# 创建保存目录，暂未利用
def create_dir():
    from os import mkdir, path
    # dir_path = "./" + str(theme)
    # if not path.exists(dir_path):
    #         mkdir(dir_path)
    # return dir_path
    if not path.exists('./papers'):
        mkdir('./papers')


# 下载pdf
def save_pdf(name_link):
    name, download_link = name_link
    name = revise_name(name)
    session = requests.session()
    resp = session.get(download_link, headers=random_user_agent(), allow_redirects=False)
    if resp.status_code == 200:  # 判断返回正常
        path = "./papers/" + str(name) + '.pdf'
        with open(path, "wb") as fp:
            fp.write(resp.content)
            sleep(5)
            fp.close()


# 保存获得的文章信息
def save_info(theme):
    df = pd.DataFrame(info_all, columns=['文章名', '引用', '摘要', '作者', '年份', 'doi', '文章链接'])
    df.to_csv('./papers/主题：%s+%i 篇.csv' % (theme, len(info_all)), encoding='utf_8_sig', index=False)


# 获得随机头
def random_user_agent():
    user_agent_list = [
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36",
        "Dalvik/1.6.0 (Linux; U; Android 4.2.1; 2013022 MIUI/JHACNBL30.0)",
        "Mozilla/5.0 (Linux; U; Android 4.4.2; zh-cn; HUAWEI MT7-TL00 Build/HuaweiMT7-TL00) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
        "Dalvik/1.6.0 (Linux; U; Android 4.3; SM-N7508V Build/JLS36C)",
        "Dalvik/1.6.0 (Linux; U; Android 4.4.4; MI 3 MIUI/V7.2.1.0.KXCCNDA)",
        "Dalvik/1.6.0 (Linux; U; Android 4.4.2; Lenovo A3800-d Build/LenovoA3800-d)",
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
    headers = {'User-Agent': choice(user_agent_list)}
    return headers


# 随机ip，目前这些IP都无效，此函数无效
def random_ip():
    resp = requests.get('https://www.89ip.cn/tqdl.html?num=60&address=&kill_address=&port=&kill_port=&isp')
    proxies_list = re.findall(
        r'(25[0-5]|2[0-4]\d|[0-1]\d{2}|[1-9]?\d)\.(25[0-5]|2[0-4]\d|[0-1]\d{2}|[1-9]?\d)\.(25[0-5]|2[0-4]\d|[0-1]\d{2}|[1-9]?\d)\.(25[0-5]|2[0-4]\d|[0-1]\d{2}|[1-9]?\d)(:-?[1-9]\d*)',
        resp.text)
    proxies_list = list(map(list, proxies_list))
    for u in range(0, len(proxies_list)):
        proxies_list[u] = '.'.join(proxies_list[u])
        proxies_list[u] = re.sub(r'.:', ":", proxies_list[u])
    proxy = "'" + choice(proxies_list) + "'"
    return proxy


# 主函数
def main_get(theme, page):
    start = time()
    urls = generate_urls(theme, page)
    if int(page) >= 6:          # 线程数最大为6，防止ip被墙
        pool = Pool(6)
    else:
        pool = Pool(int(page))
    pages = pool.map(get_pages, [url for url in urls])
    pool.close()
    for i in range(page):
        for j in range(len(pages[i])):
            info_1 = get_links(pages[i][j])
            if not info_1 is None:
                print(info_1[0])
                with Pool(6) as pool1:
                    name_link = pool1.starmap(get_papers, info_1)
                    pool1.join
                with Pool(6) as pool2:
                    pool2.map(save_pdf, [nl[0] for nl in name_link if nl != []])
    create_dir()
    save_info(theme)
    print('爬取用时: %.5f s' % (time() - start))
