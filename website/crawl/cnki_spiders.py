import random
import time

import pymysql
import redis
import requests
from bs4 import BeautifulSoup
from pymysql import IntegrityError
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
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

    # def crawl_qikan(self):
    #     """爬取期刊"""
    #     # 选择期刊
    #     try:
    #         self.driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div/div/ul/li[1]/a").click()
    #     except Exception as e:
    #         print("出现错误")
    #         print(e)
    #         return
    #     time.sleep(2)
    #     count = 0
    #     # 爬取前三页的期刊信息
    #     for i in range(3):
    #         # 获取表格行列表
    #         article_table = self.driver.find_element_by_class_name("result-table-list")
    #         article_table = article_table.find_element_by_tag_name("tbody")
    #         article_list = article_table.find_elements_by_tag_name("tr")
    #         for article in article_list:
    #             if self._row_qikan(article):
    #                 count += 1
    #         next_tag = self.driver.find_element_by_xpath('//*[@id="PageNext"]')
    #         next_tag.click()
    #         time.sleep(2)
    #     print('成功爬取{}文献'.format(count))
    def crawl_qikan(self):
        """爬取期刊"""
        try:
            # 选择期刊
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[1]/div[2]/div/div/ul/li[1]/a"))
            ).click()
            print("点击期")
            
            # 等待期刊列表加载
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "result-table-list"))
            )
            
            count = 0
            # 爬取前三页的期刊信息
            for i in range(3):
                try:
                    # 等待新页面加载完成
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "result-table-list"))
                    )
                    
                    # 等待所有行元素加载完成
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".result-table-list tbody tr"))
                    )
                    
                    # 获取当前页面所有行的数据
                    rows = self.driver.find_elements_by_css_selector(".result-table-list tbody tr")
                    
                    # 处理每一行
                    for row in rows:
                        try:
                            # 在处理每行之前确保元素仍然可交互
                            WebDriverWait(self.driver, 5).until(
                                EC.visibility_of(row)
                            )
                            
                            # 在同一行内快速获取所需的所有数据
                            title_element = row.find_element_by_css_selector(".name a")
                            source_element = row.find_element_by_css_selector(".source a")
                            date_element = row.find_element_by_css_selector(".date")
                            
                            # 获取所需的属性
                            article_href = title_element.get_attribute('href')
                            source_href = source_element.get_attribute('href')
                            publish_date = date_element.text
                            
                            # 提取URL参数
                            v_param = re.search(r'v=(.*?)(?:&|$)', article_href)
                            p_param = re.search(r'p=(.*?)(?:&|$)', source_href)
                            
                            if v_param and p_param:
                                url_article = v_param.group(1)
                                url_source = p_param.group(1)
                                
                                # 存储到Redis
                                self.r.set(url_article, publish_date)
                                
                                # 存储��MySQL
                                sql_re_as = "insert into re_article_source(url_article,url_source) " \
                                          "values('{}','{}')".format(url_article, url_source)
                                self._execute_sql(sql_re_as)
                                count += 1
                                
                        except Exception as row_e:
                            print(f"处理单行数据时出现异常: {str(row_e)}")
                            continue
                    
                    # 点击下一页
                    next_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "PageNext"))
                    )
                    next_button.click()
                    
                    # 等待页面刷新
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"爬取第{i+1}页期刊时出现异常: {str(e)}")
                    continue
                    
            print('成功爬取{}期刊'.format(count))
            
        except Exception as e:
            print(f"爬取期刊整体异常: {str(e)}")
            return

    def crawl_lunwen(self):
        """爬取论文"""
        try:
            # 等待并点击论文标签
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[1]/div[2]/div/div/ul/li[2]/a"))
            ).click()
            print("点击论文")
            
            # 等待论文列表加载
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "result-table-list"))
            )
            
            count = 0
            # 爬取前三页的论文信息
            for i in range(3):
                try:
                    # 等待新页面加载完成
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "result-table-list"))
                    )
                    
                    # 等待所有行元素加载完成
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".result-table-list tbody tr"))
                    )
                    
                    # 获取当前页面所有行的数据
                    rows = self.driver.find_elements_by_css_selector(".result-table-list tbody tr")
                    
                    # 处理每一行
                    for row in rows:
                        try:
                            # 在处理每行之前确保元素仍然可交互
                            WebDriverWait(self.driver, 5).until(
                                EC.visibility_of(row)
                            )
                            
                            # 在同一行内快速获取所需的所有数据
                            title_element = row.find_element_by_css_selector(".name a")
                            unit_element = row.find_element_by_css_selector(".unit a")
                            
                            # 获取所需的属性
                            article_href = title_element.get_attribute('href')
                            source_href = unit_element.get_attribute('href')
                            
                            # 提取URL参数
                            v_param = re.search(r'v=(.*?)(?:&|$)', article_href)
                            p_param = re.search(r'p=(.*?)(?:&|$)', source_href)
                            
                            if v_param and p_param:
                                url_article = v_param.group(1)
                                url_source = p_param.group(1)
                                
                                # 存储到MySQL
                                sql_re_as = "insert into re_article_source(url_article,url_source) " \
                                          "values('{}','{}')".format(url_article, url_source)
                                self._execute_sql(sql_re_as)
                                count += 1
                                
                        except Exception as row_e:
                            print(f"处理单行数据时出现异常: {str(row_e)}")
                            continue
                    
                    # 点击下一页
                    next_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "PageNext"))
                    )
                    next_button.click()
                    
                    # 等待页面刷新
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"爬取第{i+1}页论文时出现异常: {str(e)}")
                    continue
                    
            print('成功爬取{}论文'.format(count))
            
        except Exception as e:
            print(f"爬取论文整体异常: {str(e)}")
            return

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
        try:
            # 保存文章标题
            title_tag = article.find_element_by_class_name("name").find_element_by_tag_name("a")
            title = title_tag.text

            # 获取文章url并提取v参数
            article_href = title_tag.get_attribute('href')
            v_param = re.search(r'v=(.*?)(?:&|$)', article_href)
            if not v_param:
                print(f"无法从文章URL中提取v参数: {article_href}")
                return False
            url_article = v_param.group(1)

            # 获取来源url并提取p参数
            source = article.find_element_by_class_name('source').find_element_by_tag_name('a')
            source_href = source.get_attribute('href')
            p_param = re.search(r'p=(.*?)(?:&|$)', source_href)
            if not p_param:
                print(f"无法从来源URL中提取p参数: {source_href}")
                return False
            url_source = p_param.group(1)

            # 日期
            publish_date = article.find_element_by_class_name('date').text

        # 存储文献日期到redis
            self.r.set(url_article, publish_date)

            # 文献来源关系存储到mysql表中
            sql_re_as = "insert into re_article_source(url_article,url_source) " \
                        "values('{}','{}')".format(url_article, url_source)
            self._execute_sql(sql_re_as)
            return True
            
        except Exception as e:
            print(f"处理期刊行数据异常: {str(e)}")
            return False

    def _row_lunwen(self, article):
        """爬取论文行"""
        try:
            # 保存文章标题
            title_tag = article.find_element_by_class_name("name").find_element_by_tag_name("a")
            title = title_tag.text

            # 获取论文url并提取v参数
            article_href = title_tag.get_attribute('href')
            v_param = re.search(r'v=(.*?)(?:&|$)', article_href)
            if not v_param:
                print(f"无法从论文URL中提取v参数: {article_href}")
                return False
            url_article = v_param.group(1)

            # 获取学校来源url并提取p参数
            unit = article.find_element_by_class_name('unit').find_element_by_tag_name('a')
            source_href = unit.get_attribute('href')
            p_param = re.search(r'p=(.*?)(?:&|$)', source_href)
            if not p_param:
                print(f"无法从来源URL中提取p参数: {source_href}")
                return False
            url_source = p_param.group(1)

            # 文献来源关系存储到mysql表中
            sql_re_as = "insert into re_article_source(url_article,url_source) " \
                        "values('{}','{}')".format(url_article, url_source)
            self._execute_sql(sql_re_as)
            return True
            
        except Exception as e:
            print(f"处理论文行数据异常: {str(e)}")
            return False

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
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')

            # 添加以下选项来模拟真实浏览器
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
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
    """爬取作者详情
        返回字典：链接url，姓名name，主修专业major，总发布量sum_publish，总下载量sum_download，
        文献articles，老师teachers，学生students，所在机构organization，同机构的合作者cooperations
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
        # 添加数据库连接
        self.db = pymysql.connect(
            host=MYSQL_HOST,
            user=USERNAME,
            passwd=PASSWORD,
            db=DATABASE,
            port=MYSQL_PORT,
            charset='utf8'
        )
        
        max_retries = 3  # 最大重试次数
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 使用Selenium
                chrome_options = Options()
                chrome_options.add_argument('--headless')  # 无界面模式
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')

                # 添加以下选项来模拟真实浏览器
                chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                # 显示打开浏览器
                self.driver = webdriver.Chrome()
                print("全局等待时间设置3秒")
                self.driver.implicitly_wait(3)
                print("窗口最大化")

                # 访问作者页面
                author_url = "https://kns.cnki.net/kcms2/author/detail?" + url
                self.driver.get(author_url)
                
                # 等待页面基本元素加载
                wait = WebDriverWait(self.driver, 20, poll_frequency=1)
                element = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".doc, .author-info, .author-detail"))
                )
                
                if not element:
                    raise TimeoutException("页面关键元素未加载")
                
                # 模拟页面滚动以加载所有内容
                last_height = self.driver.execute_script("return document.body.scrollHeight")
                scroll_pause_time = random.uniform(1, 3)  # 随机等待1-3秒
                
                while True:
                    # 滚动到页面底部
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    
                    # 等待页面加载
                    time.sleep(scroll_pause_time)
                    
                    # 计算新的滚动高度并与之前的滚动高度进行比较
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        # 如果高度没有变化，说明已经到底部了
                        break
                    last_height = new_height
                    
                    # 更新等待时间
                    scroll_pause_time = random.uniform(1, 3)
                
                # 再次滚动到顶部，确保所有元素都被载
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)
                
                # 获取完整的页面内容
                page_source = self.driver.page_source
                self.soup = BeautifulSoup(page_source, 'html.parser')
                
                # 成功获取页面内容，跳出重试循环
                break
                
            except TimeoutException as te:
                print(f"页面加载超时 (尝试 {retry_count + 1}/{max_retries}): {str(te)}")
                retry_count += 1
                if self.driver:
                    self.driver.quit()
                    self.driver = None
                if retry_count < max_retries:
                    time.sleep(5 * retry_count)  # 递增等待时间
                    continue
                    
            except WebDriverException as we:
                print(f"WebDriver异常 (尝试 {retry_count + 1}/{max_retries}): {str(we)}")
                retry_count += 1
                if self.driver:
                    self.driver.quit()
                    self.driver = None
                if retry_count < max_retries:
                    time.sleep(5 * retry_count)
                    continue
                    
            except Exception as e:
                print(f"其他异常 (尝试 {retry_count + 1}/{max_retries}): {str(e)}")
                retry_count += 1
                if self.driver:
                    self.driver.quit()
                    self.driver = None
                if retry_count < max_retries:
                    time.sleep(5 * retry_count)
                    continue
                    
            # finally:
            #     # 确保driver被关闭
            #     if self.driver:
            #         try:
            #             self.driver.quit()
            #         except:
            #             pass
                    
        # 如果所有重试都失败
        if retry_count >= max_retries:
            print(f"在{max_retries}次尝试后仍无法加载页面")
            self.soup = None

    def crawl(self):
        """爬取作者详情页信息"""
        if not self.soup:
            return {
                'url': self.url,
                'name': '获取失败',
                'major': '',
                'sum_publish': 0,
                'sum_download': 0,
                'articles': [],  # 现在存储的是标题列表
                'teachers': [],
                'students': [],
                'organization': '',
                'cooperations': []
            }

        try:
            item = {'url': self.url}
            
            # 获取姓名
            item['name'] = self._crawl_name()
            
            # 获取专业领域
            item['major'] = self._crawl_major()
            
            # 获取发文量和下载量
            item['sum_publish'], item['sum_download'] = self._crawl_sum_publish_download()
                
            # 获取文章列表(期刊和博论文)
            item['articles'] = self._crawl_articles()
            
            # 获取导师信息
            item['teachers'] = self._crawl_teachers()

            # 获取学生信息
            item['students'] = self._crawl_students()
            
            # 获取所在机构
            item['organization'] = self._crawl_organization()
            
            # 获取合作作者
            item['cooperations'] = self._crawl_cooperations()
            
            return item
            
        except Exception as e:
            print(f"爬取作者详情异常: {str(e)}")
            return {
                'url': self.url,
                'name': '爬取异常',
                'major': '',
                'sum_publish': 0,
                'sum_download': 0,
                'articles': [],
                'teachers': [],
                'students': [],
                'organization': '',
                'cooperations': []
            }

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

    def _crawl_name(self):
        name_elem = self.soup.find('h1', id='showname')
        name = name_elem.text.strip() if name_elem else '未知'
        return name
    
    def _crawl_major(self):
        try:
            # 使用更精确的XPath选择器
            major_elem = self.soup.select_one('div.author-info h3:nth-of-type(2) span')
            major = "无"
            if major_elem:
                # 获取专业文本并清理
                major_text = major_elem.get_text(strip=True)
                if major_text:
                    major = major_text
                    print(f"成功获取专业领域: {major_text}")
            else:
                # 备用方案：尝试直接用XPath
                major_elem = self.soup.find('span', style=' display: inline-table;')
                if major_elem:
                    major_text = major_elem.get_text(strip=True)
                    major = major_text
                    print(f"通过备用方案获取专业领域: {major_text}")
                else:
                    print("未找到专业领域标签")
                    major = ''
                
        except Exception as e:
            print(f"获取专业领域失败: {str(e)}")
            major = ''
        return major
    
    def _crawl_sum_publish_download(self):
        try:
            stats = self.soup.find_all('em', class_='amount')
            sum_publish = 0
            sum_download = 0
            if len(stats) >= 2:
                sum_publish = int(stats[0].text) if stats[0].text.isdigit() else 0
                sum_download = int(stats[1].text) if stats[1].text.isdigit() else 0
        except:
            sum_publish = 0
            sum_download = 0
        return sum_publish, sum_download
    
    def _crawl_articles(self):
        """获取作者的所有文章标题
        Returns:
            list: 文章标题列表
        """
        articles = []
        article_urls = []
        for section_id in ['KCMS-AUTHOR-JOURNAL-LITERATURES', 'KCMS-AUTHOR-DISSERTATION-LITERATURES']:
            article_section = self.soup.find('div', id=section_id)
            if article_section:
                article_list = article_section.find_all('li')
                for article in article_list:
                    article_link = article.find('a')
                    if article_link:
                        article_title = article_link.get_text(strip=True)
                        article_url = article_link.get('href', '')
                        if article_title:
                            articles.append(article_title)
                            print(f"找到文章: {article_title}")
                        if article_url:
                            article_urls.append(article_url)
                            # print(f"找到文章URL: {article_url}")
        # 将文章的v参数提取
        article_v = []
        for article_url in article_urls:
            url_params = re.search(r'v=(.*?)(?:&|$)', article_url)
            if url_params:
                article_v.append(url_params.group(1))
        return list(set(article_v))  # 使用集合去重
    
    def _crawl_teachers(self):
        try:
            teachers = []
            teachers_urls = []
            # 先检查driver是否还活着
            if not self.driver or not hasattr(self, 'driver'):
                print("WebDriver已关闭或未初始化")
                teachers = []
                teachers_urls = []
            else:
                    
                # 使用JavaScript检查元素是否存在
                is_element_present = self.driver.execute_script("""
                    return !!document.getElementById('kcms-author-tutor');
                """)
                    
                if is_element_present:
                    # 获取渲染后的页面内容
                    # page_source = self.driver.page_source
                    # self.soup = BeautifulSoup(page_source, 'html.parser')
                    
                    # 在更新后的soup中查找导师信息
                    tutor_container = self.soup.find('div', {'id': 'kcms-author-tutor', 'class': 'module-con dis-show'})
                    if tutor_container:
                        # 在容器中找到具体的导师列表
                        tutor_list = tutor_container.find('div', {'id': 'tuhor', 'class': 'listcont'})
                        if tutor_list:
                            # 获取所有导师span标签
                            tutor_spans = tutor_list.select('ul.col4 li span')
                            for span in tutor_spans:
                                tutor_url = span.find('a')
                                if tutor_url:
                                    tutor_name = span.get_text(strip=True)
                                    if tutor_name:
                                        teachers.append(tutor_name)
                                        teachers_urls.append(tutor_url)
                                        print(f"找到导师: {tutor_name}")
                        else:
                            print("未找到导师列表容器(div#tuhor)")
                    else:
                        print("未找到导师信息容器(div#kcms-author-tutor)")
                else:
                    print("页面中不存在导师信息元素")
                    
        except Exception as e:
            print(f"获取导师信息时发生异常: {str(e)}")
            if "connection" in str(e).lower():
                print("WebDriver连接已断开，需要重新初始化")
        if not teachers:
            print("未找到任何导师")
        else:
            print(f"找到{len(teachers)}位导师")
            print(teachers)
        if not teachers_urls:
            print("未找到任何导师URL")
        else:
            print(f"找到{len(teachers_urls)}位导师URL")
            print(teachers_urls)
        return teachers_urls
    
    def _crawl_students(self):
        students = []
        student_section = self.soup.find('div', id='kcms-author-students')
        if student_section:
            student_list = student_section.find_all('li')
            for student in student_list:
                if student.text.strip():
                    students.append(student.text.strip())
        return students
    
    def _crawl_organization(self):
        try:
            organization = []
            # 使用更精确的XPath选择器获取机构信息
            org_elem = self.driver.find_element(By.XPATH, "/html/body/div[2]/div[1]/div[1]/div/div[3]/h3[1]/span/a")
            if org_elem:
                org_url = org_elem.get_attribute('href')
                org_name = org_elem.text.strip()
                    
                if org_url:
                    # 从URL中提取v参数
                    url_params = re.search(r'v=(.*?)(?:&|$)', org_url)
                    if url_params:
                        org_id = url_params.group(1)
                        print(f"成功获取所在机构URL参数: {org_id}")
                        # 可以存储org_id用于后续使用
                    
                if org_name:
                    organization = org_name
                    print(f"成功获取所在机构名称: {org_name}")
                else:
                    print("机构名称为空")
                    organization = ''
            else:
                print("未找到机构元素")
                organization = ''
                
        except NoSuchElementException:
            print("未找到指定XPath的机构元素")
            organization = ''
        except Exception as e:
            print(f"获取所在机构时发生异常: {str(e)}")
            organization = ''
        return organization

    def _crawl_cooperations(self):
        cooperations = []
        cooperations_urls = []
        coop_section = self.soup.find('div', id='cooperation')
        if coop_section:
            coop_list = coop_section.find_all('li')
            for coop in coop_list:
                author_link = coop.find('a')
                if author_link:
                    author_url = author_link.get('href', '')
                    # author_name = author_link.get_text(strip=True)
                    # if author_name:
                    #     cooperations.append(author_name)
                    #     print(f"找到合作者: {author_name}")
                    if author_url:
                        cooperations_urls.append(author_url)
                        url_params = re.search(r'v=(.*?)(?:&|$)', author_url)
                        if url_params:
                            cooperations.append(url_params.group(1))
        # 将合作者的v参数提取
        cooperations_v = []
        for coop_url in cooperations_urls:
            url_params = re.search(r'v=(.*?)(?:&|$)', coop_url)
            if url_params:
                cooperations_v.append(url_params.group(1))
        return list(set(cooperations_v))

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
            print('【dl标签异常无法获取dl标签')
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
    max_retries = 3  # 最大重试次数
    
    for url in urls:
        retries = 0
        while retries < max_retries:
            try:
                # 随机延迟1-5秒
                rand = random.uniform(1, 5)
                time.sleep(rand)
                
                author = Author(url)
                if author.soup:  # 检查是否成功初始化
                    author.store(db)
                    count += 1
                    print(f'已爬取作者页面完成：{count}/{length}')
                    break
                else:
                    print(f'作者页面初始化失败，正在重试 ({retries + 1}/{max_retries})')
                    retries += 1
                    
            except WebDriverException as e:
                print(f'【webdriver异常】{str(e)}')
                retries += 1
                if retries < max_retries:
                    print(f'正在重试 ({retries}/{max_retries})')
                    time.sleep(5)  # 异常后等待更长时间
                continue
            except Exception as e:
                print(f'【其他异常】{str(e)}')
                retries += 1
                if retries < max_retries:
                    print(f'正在重试 ({retries}/{max_retries})')
                    time.sleep(5)
                continue
                
        if retries == max_retries:
            print(f'URL {url} 达到最大重试次数，跳过')


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
