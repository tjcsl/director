from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^$", views.index_view, name="docs_home"),
    url("new", views.new_article_view, name="new_article"),
    url("(?P<article_slug>[\w-]+)/$", views.read_article_view, name="read_article"),
    url("(?P<article_slug>[\w-]+)/edit$", views.edit_article_view, name="edit_article"),
]
