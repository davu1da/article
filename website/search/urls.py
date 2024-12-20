from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = 'search'
urlpatterns = [
    # path=/polls/
    # path('', views.index, name='index'),
    path('', views.index, name='index'),
    path('article/<str:articleurl>', views.articleDetail, name='article'),
    path('author/<str:authorurl>', views.authorDetail, name='author'),
    path('organization/<str:organizationUrl>', views.organizationDetail, name='organization'),
    path('source/<str:sourceUrl>', views.sourceDetail, name='source'),
    path('<str:keyword>', views.search, name='search'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
