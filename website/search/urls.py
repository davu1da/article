from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

# 定义当前应用的名称为 'search'，用于命名空间和反向解析URL
app_name = 'search'

# 定义URL模式列表 urlpatterns，包含多个路径映射
urlpatterns = [
    # 主页路径，对应根路径 '/'
    path('', views.index, name='index'),

    # 文章详情页面路径，包含一个字符串参数 articleurl
    path('article/<str:articlename>', views.articleDetail, name='article'),

    # 作者详情页面路径，包含一个字符串参数 authorurl
    path('author/<str:authorname>', views.authorDetail, name='author'),

    # 组织详情页面路径，包含一个字符串参数 organizationUrl
    path('organization/<str:organizationUrl>', views.organizationDetail, name='organization'),

    # 来源详情页面路径，包含一个字符串参数 sourcename
    path('source/<str:sourcename>', views.sourceDetail, name='source'),

    # 搜索建议路径，包含一个字符串参数 keyword
    path('suggest/<str:keyword>', views.get_search_suggestion_2, name='suggest'),

    path('setcraw/', views.set_craw, name='set_craw'),
    
    path('crawl', views.crawl, name='crawl'),
    # 搜索页面路径，包含一个字符串参数 keyword
    path('<str:keyword>', views.search, name='search'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)