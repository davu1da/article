# Create your views here.
from django.shortcuts import render

from .searchNeo4j import *

from .kimi_api import *

import redis

import subprocess

REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379

g = Graph("bolt://localhost:7687", auth=("neo4j", "12345678"))

# 连接redis数据库
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def index(request):
    search_suggestion = get_search_suggestion()
    return render(request, 'search/index.html', {'search_suggestion': search_suggestion})
    # return render(request, 'search/index.html')

# def suggestion(request):
#     return render(request, 'search/index.html', {'search_suggestion': search_suggestion})

def crawl(request):
    return render(request, 'search/crawl.html')
def search(request, keyword):
    articles = searchArticle(g, keyword)
    # search_suggestion = get_search_suggestion(keyword)
    # return render(request, 'search/results.html', {'articles': articles})
    return render(request, 'search/results.html', {
        'articles': articles,
        'keyword': keyword,
        # 'search_suggestion': search_suggestion
    })


def articleDetail(request, articlename):
    # 从redis中获取文章url
    print(articlename)
    # 判断是否是一个链接
    # 是否存在dbcode字符
    if articlename.find("FileName"):
        articleurl = articlename
    elif articlename.find("dbcode"):
        articleurl = articlename
    # if articlename.find("dbcode"):
    #     articleurl = articlename
    else:
        articleurl = r.get(articlename)
    print(articleurl)
    if articleurl is None:
        return render(request, 'search/article.html')
    # print(articleurl)
    article = getArticleDetail(articleurl)
    authors = getAus(articleurl)
    # 相关文章
    reArticles = getReArticles(articleurl)[0:7]
    # 相关学者
    reAuthors = getReAuthors(articleurl)
    return render(request, 'search/article.html',
                  {'article': article, 'authors': authors, 'reArticles': reArticles, 'reAuthors': reAuthors})


def authorDetail(request, authorname):
    # 如果authorname是一个链接，则直接返回该链接对应的页面
    print(authorname)
    if authorname.find("code"):
        authorurl = authorname
    elif authorname.find("skey"):
        authorurl = authorname
    else:
        authorurl = r.get(authorname)
    if authorurl is None:
        return render(request, 'search/author.html')
    author = getAuthorDetail(authorurl)
    res = getAuO(authorurl)
    organization = res[0] if len(res) > 0 else Organization()
    # 导师
    teachers = getATeachers(authorurl)
    # 学生
    students = getAStudents(authorurl)
    # 发布的文章
    articles = getAArticles(authorurl)
    # 同机构的合作者
    co = getACo(authorurl)
    return render(request, 'search/author.html',
                  {'author': author, 'organization': organization, 'articles': articles, 'teachers': teachers,
                   'students': students, 'co': co})


def organizationDetail(request, organizationUrl):
    organization = getOrganizationDetail(organizationUrl)
    authors = getOAu(organizationUrl)[0:100]
    return render(request, 'search/organization.html', {'organization': organization, 'authors': authors})


def sourceDetail(request, sourcename):
    
    
    # 如果sourcename里面含有字符"q=" ,flag = true
    flag = "q=" in sourcename
    
    if flag:
        # print("没有转换======================================")
        sourceUrl = sourcename
    else:
        # print("进入转换========================================================")
        sourceUrl = r.get(sourcename)
    # print(sourceUrl)
    source = getSourceDetail(sourceUrl)
    return render(request, 'search/source.html', {'source': source})


@csrf_exempt
def set_craw(request):
    if request.method == 'POST':
        try:
            # 确保 body 不为空
            if not request.body:
                return JsonResponse({'success': False, 'error': 'Empty request body'}, status=400)

            data = json.loads(request.body)
            
            # 检查并获取参数，设置默认值
            keyword = data.get('keyword', '')
            frequency = data.get('frequency', 1)  # 默认频率为1
            frequency_unit = data.get('frequency_unit', 'hours')  # 默认单位为小时
            
            # 验证 frequency_unit 的合法性
            valid_units = ['minutes', 'hours', 'days']
            if frequency_unit not in valid_units:
                return JsonResponse({'success': False, 'error': 'Invalid frequency unit'}, status=400)

            # 日志记录
            print(f"Received settings: keyword={keyword}, frequency={frequency}, frequency_unit={frequency_unit}")

            # 构建命令行命令
            venv_path = 'c:/Users/Sunshine/softwaredesign/docsearch-master/.venv/Scripts/activate'
            crawler_script = 'c:/Users/Sunshine/softwaredesign/docsearch-master/run_crawler.py'
            command = [
                'cmd.exe', '/c', f'call {venv_path} && python {crawler_script}',
                '--keyword', str(keyword),
                '--frequency', str(frequency),
                '--frequency_unit', frequency_unit
            ]

            # 执行命令行命令
            process = subprocess.Popen(command, shell=True)
            print(f"Started crawler with PID: {process.pid}")

            return JsonResponse({'success': True})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f"Error setting crawl settings: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
