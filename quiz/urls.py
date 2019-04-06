from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
]

from . import views

app_name = 'quiz'
urlpatterns = [
    # ex: /quiz/
    url(r'^$', views.index, name='index'),
    # ex: /quiz/5/
    url(r'^(?P<level>[0-9]+)/$', views.detail, name='detail'),
    # ex: /quiz/5/results/1/
    url(r'^(?P<level>[0-9]+)/results/(?P<choice>[1-5])/$', views.results, name='results'),
]
