import random
import time

import pymysql
import redis
import requests
from bs4 import BeautifulSoup
from pymysql import IntegrityError
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from website.crawl.utils import *

MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = 3306
USERNAME = "root"
PASSWORD = "123456"
DATABASE = "cnkidemo"

REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379

# 测试文件用
PATH = './crawl/static/img/'


class KeyList:
    """关键词列表
    爬取关系，文献发表日期
    关系：文献-来源，文献-作者，存入MySQL关系表中
    发布日期：爬取后存入redis或者直接爬取
    """

    def __init__(self):
        self.driver = webdriver.Chrome()
        self.driver.get("https://www.cnki.net/")
        print("全局等待时间设置3秒")
        self.driver.implicitly_wait(3)
        print("窗口最大化")
        self.driver.maximize_window()
        self.db = pymysql.connect(host=MYSQL_HOST, user=USERNAME, passwd=PASSWORD, db=DATABASE, port=MYSQL_PORT,
                                  charset='utf8')
        self.curr = self.db.cursor()
        self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    # def input_keyword(self, keyword):
    #     """输入关键词"""
    #     print("输入的关键词为：{}".format(keyword))
    #     key_input = self.driver.find_element_by_id("txt_SearchText")
    #     key_input.send_keys(keyword)
    #     key_input.send_keys(Keys.RETURN)
    
    def input_keyword(self, keyword):
        """输入关键词"""
        try:
            # 等待搜索框出现
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "txt_SearchText"))
            )
            key_input = self.driver.find_element_by_id("txt_SearchText")
            key_input.send_keys(keyword)
            key_input.send_keys(Keys.RETURN)
        except Exception as e:
            print(f"输入关键词异常: {str(e)}")
            raise

    def crawl_qikan(self):
        """爬取期刊"""
        # 选择期刊
        try:
            self.driver.find_element_by_xpath("/html/body/div[5]/div[1]/div/ul[1]/li[1]/a").click()
        except Exception as e:
            print("出现错误")
            print(e)
            return
        time.sleep(2)
        count = 0
        # 爬取前三页的期刊信息
        for i in range(3):
            # 获取表格行列表
            article_table = self.driver.find_element_by_class_name("result-table-list")
            article_table = article_table.find_element_by_tag_name("tbody")
            article_list = article_table.find_elements_by_tag_name("tr")
            for article in article_list:
                if self._row_qikan(article):
                    count += 1
            next_tag = self.driver.find_element_by_xpath('//*[@id="PageNext"]')
            next_tag.click()
            time.sleep(2)
        print('成功爬取{}文献'.format(count))

    def crawl_lunwen(self):
        """爬取论文"""
        try:
            self.driver.find_element_by_xpath("/html/body/div[5]/div[1]/div/ul[1]/li[2]/a").click()
            print("点击论文")
        except Exception as e:
            print(e)
            return
        time.sleep(2)
        count = 0
        for i in range(3):
            # 获取表格行列表
            article_table = self.driver.find_element_by_class_name("result-table-list")
            article_table = article_table.find_element_by_tag_name("tbody")
            article_list = article_table.find_elements_by_tag_name("tr")
            for article in article_list:
                if self._row_lunwen(article):
                    count += 1
            # 爬取论文行数据并存入mysql相应关系表
            next_tag = self.driver.find_element_by_xpath('//*[@id="PageNext"]')
            next_tag.click()
            time.sleep(2)
        print('成功爬取{}论文'.format(count))

    def crawl(self, keyword):
        """爬取本列表的期刊和论文"""
        self.input_keyword(keyword)
        self.crawl_qikan()
        self.crawl_lunwen()
        # 关闭资源
        self.driver.close()
        self.db.close()
        self.r.close()

    def _row_qikan(self, article):
        """爬取期刊行"""
        # 保存文章标题
        title_tag = article.find_element_by_class_name("name").find_element_by_tag_name("a")
        title = title_tag.text

        # 获取文章url
        url_article = title_tag.get_attribute('href')
        url_article = articleToUrl(url_article)
        if url_article == '#':
            return False

        # # 作者url
        # author_list_a = article.find_element_by_class_name("author").find_elements_by_tag_name("a")
        # authors = []
        # for author_a in author_list_a:
        #     # sfield=au&skey=原雯&code=45345959
        #     name = author_a.text
        #     name_url = "sfield=au&skey=" + name + "&code="
        #     try:
        #         href = author_a.get_attribute('href')
        #         code = extractAuthorCode(href)
        #         name_url = name_url + code
        #         # 提取code
        #         authors.append(name_url)
        #     except NoSuchElementException:
        #         authors.append('#')

        # 刊名，链接
        source = article.find_element_by_class_name('source').find_element_by_tag_name('a')
        source_name = source.text
        source_href = source.get_attribute('href')
        url_source = sourceToUrl(source_href)

        # 日期
        publish_date = article.find_element_by_class_name('date').text
        # print(title)

        # 存储文献日期到redis
        self.r.set(url_article, publish_date)

        # # 文献作者关系存储到mysql表
        # for url_author in authors:
        #     sql_re_aa = "insert into re_article_author(url_article,url_author) " \
        #                 "values('{}','{}')".format(url_article, url_author)
        #     self._execute_sql(sql_re_aa)

        # 文献来源关系存储到mysql表中
        sql_re_as = "insert into re_article_source(url_article,url_source) " \
                    "values('{}','{}')".format(url_article, url_source)
        self._execute_sql(sql_re_as)
        return True

    def _row_lunwen(self, article):
        """爬取期刊行"""
        # 保存文章标题
        title_tag = article.find_element_by_class_name("name").find_element_by_tag_name("a")
        title = title_tag.text

        # 获取论文url
        url_article = title_tag.get_attribute('href')
        url_article = lunwenToUrl(url_article)
        if url_article == '#':
            return False

        # 获取学校来源url
        unit = article.find_element_by_class_name('unit').find_element_by_tag_name('a')
        school_name = unit.text
        source_href = unit.get_attribute('href')
        url_school = sourceToUrl(source_href)

        # 文献来源关系存储到mysql表中
        sql_re_as = "insert into re_article_source(url_article,url_source) " \
                    "values('{}','{}')".format(url_article, url_school)
        self._execute_sql(sql_re_as)
        return True

    def _execute_sql(self, sql):
        """执行SQL语句
        :param sql: 要执行的sql语句
        """
        try:
            # 执行sql语句
            self.curr.execute(sql)
            # 提交到数据库执行
            self.db.commit()
            print('【成功】{}'.format(sql))
        except Exception as e:
            # 如果发生错误则回滚
            self.db.rollback()
            print('【异常】{}'.format(sql))


class CrawlBase:
    def __init__(self):
        pass

    def crawl(self):
        pass

    def store(self, db):
        pass


class Article(CrawlBase):
    """文章详情页
    发布日期以键值对形式存到Redis
    直接获取到的信息：标题，摘要，关键词
    作者链接
    """

    # def __init__(self, url="FileName=XAJD20210319000&DbName=CAPJLAST&DbCode=CAPJ&"):
    #     super().__init__()
    #     self.url = url
    #     headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0"}
    #     try:
    #         req = requests.get("https://kns.cnki.net/kcms/detail/detail.aspx?" + url, headers=headers)
    #         soup = BeautifulSoup(req.text, 'html5lib')
    #         self.doc = soup.find('div', class_="doc-top")
    #         if not self.doc:
    #             print(f"警告: 无法获取文章详情页面内容 URL:{url}")
    #         self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    #     except Exception as e:
    #         print(f"初始化Article异常: {str(e)}")
    #         self.doc = None
    #         self.r = None
    def __init__(self, url="FileName=XAJD20210319000&DbName=CAPJLAST&DbCode=CAPJ&"):
        super().__init__()
        self.url = url
        
        try:
            # 使用Selenium
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 无界面模式
            chrome_options.add_argument('--disable-gpu')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.get("https://kns.cnki.net/kcms/detail/detail.aspx?" + url)
            
            # 等待页面加载
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "doc-top"))
            )
            
            # 获取渲染后的页面内容
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html5lib')
            self.doc = soup.find('div', class_="doc-top")
            
        except Exception as e:
            print(f"初始化Article异常: {str(e)}")
            self.doc = None
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()
        
        self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    def crawl(self):
        """爬取文章详情页
        返回字典类型数据，链接url，标题title，摘要summary，关键词keys，作者authors，发布日期date
        """
        # 获取文章标题
        # item = {'title': self.doc.h1.text, 'url': self.url}
        if not self.doc:
            return {'title': '获取失败', 'url': self.url, 'authors': [], 'summary': '', 'keys': '', 'date': None}
            
        try:
            item = {'title': self.doc.h1.text if self.doc.h1 else '无标题', 'url': self.url}

            author_list_tag = self.doc.find('h3', id="authorpart")  # 作者列表
            authors = []
            if not author_list_tag:
                pass
            else:
                for author_tag in author_list_tag:
                    try:
                        # 作者可能没有href
                        href = author_tag.a.get('onclick')
                        # name = re.sub(r'\d+,\d+', '', author_tag.text)
                        url = auToUrl(href)
                        authors.append(url)
                    except:
                        continue
            if 'CMFD' in self.url or 'CDFD' in self.url:
                # 论文的作者只有一个
                try:
                    a_tag = self.doc.find('a', class_='author')
                    href = a_tag.get('onclick')
                    url = auToUrl(href)
                    authors.append(url)
                except:
                    # 作者无链接
                    pass
            item['authors'] = authors

            summary_tag = self.doc.find('span', id='ChDivSummary')
            item['summary'] = summary_tag.text if summary_tag else ''

            # 判断是否有关键词
            flag = self.doc.find('p', class_='keywords')
            if flag:
                # 直接从隐藏的input标签获取关键词
                keyword_input = self.doc.find('input', {'id': 'keywordcnvalue'})
                if keyword_input and keyword_input.get('value'):
                    # 使用;;分割关键词
                    key_list = keyword_input.get('value').split(';;')
                    item['keys'] = str(key_list)
                else:
                    # 如果找不到input标签,直接从p标签文本分割
                    keywords_text = flag.text.strip()
                    key_list = [k.strip() for k in keywords_text.split(';') if k.strip()]
                    item['keys'] = str(key_list)
            else:
                item['keys'] = ''
            item['date'] = self.r.get(self.url)
            self.r.close()
            return item
        except Exception as e:
            print(f"爬取文章详情异常: {str(e)}")
            return {'title': '爬取异常', 'url': self.url, 'authors': [], 'summary': '', 'keys': '', 'date': None}

    def store(self, db):
        """存储数据表：article，re_article_author"""
        item = self.crawl()
        url = item['url']
        title = item['title']
        summary = item['summary']
        keywords = re.sub(r"\[|\]|'", '', item['keys'])
        date = item['date'] if item['date'] else '2020-01-01'
        sql_a = "insert into article(url, title, summary, keywords, date) " \
                "VALUES ('{}','{}','{}','{}','{}')".format(url, title, summary, keywords, date)
        executeSql(db, sql_a)
        for au in item['authors']:
            sql_re_aa = "insert into re_article_author(url_article, url_author) " \
                        "VALUES ('{}','{}')".format(url, au)
            executeSql(db, sql_re_aa)


class Author(CrawlBase):
    """作者详情页
    信息：主修专业，总发文量，总下载量
    关系：作者-文献，师生，所在机构，同机构的合作者
    """

    def __init__(self, url):
        """初始化作者类
        Args:
            url: 作者链接
        """
        super().__init__()
        self.url = url
        self.driver = None
        self.soup = None
        
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)  # 设置页面加载超时
            
            # 访问作者页面
            author_url = "https://kns.cnki.net/old/kcms2/author/detail?" + url
            self.driver.get(author_url)
            
            # 等待页面加载
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "kcms-author-info"))
            )
            
            # 获取页面内容
            page_source = self.driver.page_source
            self.soup = BeautifulSoup(page_source, 'html.parser')
            
        except Exception as e:
            print(f"初始化Author异常: {str(e)}")
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
            self.soup = None

    def crawl(self):
        """爬取作者详情
        Returns:
            dict: 包含作者信息的字典
        """
        default_result = {
            'url': self.url,
            'name': '获取失败',
            'major': '',
            'sum_publish': 0,
            'sum_download': 0,
            'articles': []
        }
        
        if not self.soup:
            return default_result
        
        try:
            item = {'url': self.url}
            
            # 获取作者基本信息区域
            author_info = self.soup.find('div', id='kcms-author-info')
            if not author_info:
                return default_result
            
            # 获取姓名
            name_elem = author_info.find('h1', id='showname')
            item['name'] = name_elem.text.strip() if name_elem else '未知'
            
            # 获取专业领域
            major_elem = author_info.find('h3', class_='expert-field')
            if major_elem and major_elem.find('span'):
                item['major'] = major_elem.find('span').text.strip()
            else:
                item['major'] = ''
            
            # 获取发文量和下载量
            try:
                stats = author_info.find_all('div', class_='amount')
                if len(stats) >= 2:
                    item['sum_publish'] = int(stats[0].text) if stats[0].text.isdigit() else 0
                    item['sum_download'] = int(stats[1].text) if stats[1].text.isdigit() else 0
            except:
                item['sum_publish'] = 0
                item['sum_download'] = 0
            
            # 获取文章列表
            articles = []
            article_section = self.soup.find('div', id='KCMS-AUTHOR-JOURNAL-LITERATURES')
            if article_section:
                article_list = article_section.find_all('li')
                for article in article_list:
                    article_link = article.find('a')
                    if article_link:
                        article_url = article_link.get('href', '')
                        if article_url:
                            # 从href中提取文章URL参数
                            url_params = re.search(r'v=(.*?)&', article_url)
                            if url_params:
                                articles.append({
                                    'title': article_link.text.strip(),
                                    'url': url_params.group(1)
                                })
                            
            item['articles'] = articles
            
            return item
            
        except Exception as e:
            print(f"爬取作者详情异常: {str(e)}")
            return default_result

    def close(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"关闭浏览器异常: {str(e)}")
            finally:
                self.driver = None

    def store(self, db):
        """存储数据表：author，re_article_author"""
        try:
            item = self.crawl()
            
            # 构建作者基本信息SQL
            url = item['url']
            name = item['name']
            major = item['major']
            sum_publish = item['sum_publish']
            sum_download = item['sum_download']
            
            sql_a = """INSERT INTO author(url, name, major, sum_publish, sum_download) 
                    VALUES (%s, %s, %s, %s, %s)"""
            try:
                curr = db.cursor()
                curr.execute(sql_a, (url, name, major, sum_publish, sum_download))
                db.commit()
            except pymysql.IntegrityError:
                print(f"作者记录已存在: {url}")
            except Exception as e:
                print(f"插入作者记录异常: {str(e)}")
                db.rollback()
                
            # 存储文章作者关系
            for article in item['articles']:
                article_url = article['url']
                sql_aa = """INSERT INTO re_article_author(url_article, url_author) 
                        VALUES (%s, %s)"""
                try:
                    curr = db.cursor()
                    curr.execute(sql_aa, (article_url, url))
                    db.commit()
                except pymysql.IntegrityError:
                    print(f"文章作者关系已存在: {article_url} - {url}")
                except Exception as e:
                    print(f"插入文章作者关系异常: {str(e)}")
                    db.rollback()
                
        except Exception as e:
            print(f"存储作者数据异常: {str(e)}")


class Source(CrawlBase):
    """文献来源
    信息：名称，基本信息，出版信息，评估信息
    关系：文献链接
    """

    def __init__(self, url):
        super().__init__()
        self.url = url
        # newurl = 'https://kns.cnki.net/KNS8/Navi?' + url
        # headers = {
        #     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"}
        # req = requests.get(newurl, headers=headers)
        # soup = BeautifulSoup(req.text, 'html.parser')
        # # 通过分析页面信息，要爬取的信息都存在dl标签中
        # self.dl = soup.dl
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.get('https://kns.cnki.net/KNS8/Navi?' + url)
            
            # 等待页面加载
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "dl"))
            )
            
            # 获取渲染后的页面内容
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            self.dl = soup.dl
            
            if not self.dl:
                print(f'警告: 无法获取来源页面内容 URL:{url}')
                
        except Exception as e:
            print(f'初始化Source异常: {str(e)}')
            self.dl = None
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()

    def crawl(self):
        item = {'url': self.url}
        if not self.dl:
            print('【dl标签异常】无法获取dl标签')
            return
        name_tag = self.dl.h3
        name = name_tag.text if name_tag else ''

        name_en_tag = name_tag.p
        name_en = name_en_tag.text if name_en_tag else ''
        temp = re.sub(r'\s', '', name_en) if name_en else ''
        item['name'] = re.sub(r'\s*|{}'.format(temp), '', name)
        item['name'] = item['name'].replace(temp, '')
        item['name'] = re.sub(r'\d*', '', item['name'])
        item['en-name'] = name_en
        uls = self.dl.findAll('ul')
        if len(uls) == 2:
            # 基本信息,出版概况
            basic = uls[0].text
            publish = uls[1].text
            basic = re.sub(r'基本信息|\s*', '', basic)
            publish = re.sub(r'出版概况|\s', '', publish)
            item['basic'] = basic
            item['publish'] = publish
            item['evaluation'] = ''
        elif len(uls) == 3:
            # 基本信息，出版信息，评价信息
            basic = uls[0].text
            publish = uls[1].text
            evaluation = uls[2].text
            basic = re.sub(r'基本信息|\s*', '', basic)
            publish = re.sub(r'出版信息|\s*', '', publish)
            evaluation = re.sub(r'评价信息|\s*', '', evaluation)
            item['basic'] = basic
            item['publish'] = publish
            item['evaluation'] = evaluation
        else:
            item['basic'] = ''
            item['publish'] = ''
            item['evaluation'] = ''

        return item

    def store(self, db):
        item = self.crawl()
        if not item:
            return
        url = item['url']
        name = item['name']
        basic = item['basic']
        publish = item['publish']
        evaluation = item['evaluation']
        sql = "insert into source(url, name, basic_info, publish_info, evaluation) " \
              "VALUES ('{}','{}','{}','{}','{}')".format(url, name, basic, publish, evaluation)
        executeSql(db, sql)


class Organization(CrawlBase):
    """作者机构
    直接获取的信息：名称，曾用名，地域，官网
    机构主要作者,主办刊物
    """

    # todo 爬取作者机构详情
    def __init__(self, url):
        super().__init__()
        self.url = url
        # new_url = 'https://kns.cnki.net/kcms/detail/knetsearch.aspx?' + url
        # headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0"}
        # req = requests.get(new_url, headers=headers)
        # self.soup = BeautifulSoup(req.text, 'html.parser')
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.get('https://kns.cnki.net/kcms/detail/knetsearch.aspx?sfield=in&' + url)
            
            # 等待页面加载
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "orginfo"))
            )
            
            # 获取渲染后的页面内容
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            self.doc = soup
            
        except Exception as e:
            print(f'初始化Organization异常: {str(e)}')
            self.doc = None
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()

    def crawl(self):
        item = {'url': self.url, 'name': self.doc.h1.text if self.doc.h1 else ''}

        # 获取主要信息的div
        rowall = self.doc.find('div', class_='rowall')

        # 获取曾用名，地域，网址
        if rowall:
            used_name_span = rowall.find('span', string=re.compile('曾用名'))
            region_span = rowall.find('span', string=re.compile('地域'))
            website = rowall.find('span', string=re.compile('网址'))
            if used_name_span:
                item['used_name'] = used_name_span.next_sibling.text if used_name_span.next_sibling else ''
            else:
                item['used_name'] = ''
            if region_span:
                item['region'] = region_span.next_sibling.text if region_span.next_sibling else ''
            else:
                item['region'] = ''
            if website:
                item['website'] = website.next_sibling.text if website.next_sibling else ''
            else:
                item['website'] = ''
        else:
            item['used_name'] = ''
            item['region'] = ''
            item['website'] = ''

        # 如果有logo就下载下来
        logo_div = self.doc.find('div', class_="organ-logo")
        if logo_div:
            try:
                img = logo_div.find('img')
                src = img.get('src')
                imgurl = re.sub(r'\s', '', src)
                # print(os.getcwd())
                req1 = requests.get(imgurl)
                path = PATH + item['name'] + '.jpg'
                f = open(path, 'wb')
                f.write(req1.content)
                f.close()
            except Exception as e:
                print('存取图片异常')
                raise e
        else:
            print('{},无logo'.format(item['name']))
        return item

    def store(self, db):
        item = self.crawl()
        url = item['url']
        name = item['name']
        used_name = item['used_name']
        region = item['region']
        website = item['website']
        sql = "INSERT INTO organization(url,name,used_name,region,website) " \
              "VALUES ('{}','{}','{}','{}','{}')".format(url, name, used_name, region, website)
        executeSql(db, sql)


def executeSql(db, sql):
    """执行sql语句"""
    try:
        curr = db.cursor()
        # 执行sql语句
        curr.execute(sql)
        # 提交到数据库执行
        db.commit()
        print('【成功】{}'.format(sql))
    except IntegrityError as ie:
        print('【异常】此条记录已存在！{}'.format(sql))
    except Exception as e:
        # 如果发生错误则回滚
        db.rollback()
        print('【异常】{}'.format(sql))


def getArticleUrls(db):
    """获取未被爬取的文献链接"""
    # sql1 = "SELECT DISTINCT article.url FROM article LEFT JOIN re_article_author ON article.url=re_article_author.url_article WHERE re_article_author.url_article is NULL"
    sql = 'SELECT DISTINCT re_article_source.url_article ' \
          'FROM re_article_source ' \
          'LEFT JOIN article ON re_article_source.url_article=article.url ' \
          'WHERE article.url is NULL'
    curr = db.cursor()
    curr.execute(sql)
    urls = []
    for data in curr.fetchall():
        url = data[0]
        urls.append(url)

    sql2 = 'SELECT DISTINCT re_article_author.url_article ' \
           'FROM re_article_author ' \
           'LEFT JOIN article ON re_article_author.url_article=article.url ' \
           'WHERE article.url is NULL'
    curr.execute(sql2)
    for data in curr.fetchall():
        url = data[0]
        urls.append(url)
    return urls


def crawlArticle(urls, db):
    """爬取未被爬取的文章"""
    length = len(urls)
    count = 0
    if(int(length) == 0):
        assert False, "没有需要爬取的文献"  

    print("需要爬取的文献个数为 {}".format(length))
    for url in urls:
        rand = random.random()
        time.sleep(rand)
        article = Article(url)
        # item = a.crawl()
        article.store(db)
        count += 1
        print('已爬取文章页面完成：{}/{}'.format(count, length))
        # print(item)


def getAuthorsUrls(db):
    """获取未被爬取的作者链接"""
    sql_aa = 'SELECT DISTINCT re_article_author.url_author ' \
             'FROM re_article_author ' \
             'LEFT JOIN author ON re_article_author.url_author=author.url ' \
             'WHERE author.url is NULL'
    sql_ao = """
                SELECT DISTINCT
                    re_author_organization.url_author
                FROM
                    re_author_organization
                LEFT JOIN author ON re_author_organization.url_author = author.url
                WHERE
                    author.url IS NULL
                """
    curr = db.cursor()
    curr.execute(sql_aa)
    urls = []
    for data in curr.fetchall():
        url = data[0]
        urls.append(url)
    curr.execute(sql_ao)
    for data in curr.fetchall():
        url = data[0]
        urls.append(url)
    return urls


def getAuthorsUrls_ts(db):
    """师生关系表中未被爬取的作者"""
    sql_at = """SELECT DISTINCT
                    url_teacher
                FROM
                    `re_teacher_student`
                WHERE
                    url_teacher NOT IN (SELECT url FROM author);
            """
    sql_as = """SELECT DISTINCT
                        url_student
                    FROM
                        `re_teacher_student`
                    WHERE
                        url_student NOT IN (SELECT url FROM author);
                """
    curr = db.cursor()
    curr.execute(sql_at)
    urls = []
    for data in curr.fetchall():
        url = data[0]
        urls.append(url)
    curr.execute(sql_as)
    for data in curr.fetchall():
        url = data[0]
        urls.append(url)
    return urls


def crawlAuthor(urls, db):
    """爬取未被爬取的作者"""

    length = len(urls)
    count = 0
    for url in urls:
        rand = random.randint(1, 5)
        time.sleep(rand)
        try:
            author = Author(url)
            author.store(db)
            author.close()
            count += 1
            print('已爬取作者页面完成：{}/{}'.format(count, length))
        except WebDriverException as web:
            print('【webdriver异常】' + web.msg)
            continue


def getSourceUrls(db):
    """获取未被爬取的文献来源链接"""
    sql = """
            SELECT DISTINCT
                re_article_source.url_source
            FROM
                re_article_source
            LEFT JOIN source ON re_article_source.url_source = source.url
            WHERE
                source.url IS NULL
	        """
    # sql = 'SELECT DISTINCT re_article_source.url_source FROM re_article_source LEFT JOIN source ON re_article_source.url_article=source.url WHERE source.url is NULL'
    curr = db.cursor()
    curr.execute(sql)
    urls = []
    for data in curr.fetchall():
        url = data[0]
        urls.append(url)
    return urls


def crawlSource(urls, db):
    """爬取未被爬取的文献来源"""
    print("需要爬取的文献来源个数为 {}".format(len(urls)))
    for url in urls:
        time.sleep(2)
        source = Source(url)
        source.store(db)


def getOrganizationUrls(db):
    """获取未被爬取的作者所在机构链接"""
    urls = []
    sql_ao = """
                    SELECT DISTINCT
                        re_author_organization.url_organization
                    FROM
                        re_author_organization
                    LEFT JOIN organization ON re_author_organization.url_organization = organization.url
                    WHERE
                        organization.url IS NULL
                    """
    curr = db.cursor()
    curr.execute(sql_ao)
    for data in curr.fetchall():
        url = data[0]
        urls.append(url)
    return urls


def crawlOrganization(urls, db):
    """爬取未被爬取的学者所在单位"""
    print("需要爬取的文献来源个数为 {}".format(len(urls)))
    for url in urls:
        rand = random.random()
        time.sleep(rand)
        organization = Organization(url)
        organization.store(db)


def main(db):
    """爬虫主程序"""
    while True:
        urls_1 = getArticleUrls(db)
        crawlArticle(urls_1, db)
        # urls_2 = getAuthorsUrls(db)
        # crawlAuthor(urls_2, db)
        # urls_3 = getAuthorsUrls_ts(db)
        # crawlAuthor(urls_3, db)
        # urls_3 = getSourceUrls(db)
        # crawlSource(urls_3, db)
        # urls_4 = getOrganizationUrls(db)
        # crawlOrganization(urls_4, db)
