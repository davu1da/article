from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

# 定义当前应用的名称为 'search'，用于命名空间和反向解析URL
app_name = 'search'

# 定义URL模式列表 urlpatterns，包含多个路径映射
urlpatterns = [

    # 主页路径，对应根路径 '/'
    # 当访问 '/' 时，调用 views.index 视图函数，并命名为 'index'
    path('', views.index, name='index'),

    # 文章详情页面路径，包含一个字符串参数 articleurl
    # 当访问 '/article/<articleurl>' 时，调用 views.articleDetail 视图函数，并命名为 'article'
    path('article/<str:articleurl>', views.articleDetail, name='article'),

    # 作者详情页面路径，包含一个字符串参数 authorurl
    # 当访问 '/author/<authorurl>' 时，调用 views.authorDetail 视图函数，并命名为 'author'
    path('author/<str:authorurl>', views.authorDetail, name='author'),

    # 组织详情页面路径，包含一个字符串参数 organizationUrl
    # 当访问 '/organization/<organizationUrl>' 时，调用 views.organizationDetail 视图函数，并命名为 'organization'
    path('organization/<str:organizationUrl>', views.organizationDetail, name='organization'),

    # 来源详情页面路径，包含一个字符串参数 sourceUrl
    # 当访问 '/source/<sourceUrl>' 时，调用 views.sourceDetail 视图函数，并命名为 'source'
    path('source/<str:sourceUrl>', views.sourceDetail, name='source'),

    # 搜索页面路径，包含一个字符串参数 keyword
    # 当访问 '/<keyword>' 时，调用 views.search 视图函数，并命名为 'search'
    path('<str:keyword>', views.search, name='search'),

# 添加静态文件的URL配置，用于在开发环境中提供静态文件
# settings.STATIC_URL 是静态文件的URL前缀，settings.STATIC_ROOT 是静态文件的实际存储路径
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
