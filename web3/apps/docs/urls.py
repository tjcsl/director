from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^$", views.index_view, name="docs_home"),
    url("new/$", views.new_article_view, name="new_article"),
    url("^list/$", views.list_articles_view, name="list_articles"),
    url("(?P<article_slug>[\w-]+)/$", views.read_article_view, name="read_article"),
    url("(?P<article_slug>[\w-]+)/save$", views.save_view, name="save_article"),
    url("(?P<article_slug>[\w-]+)/save_revision$", views.save_history_view, name="save_history_article"),
    url("(?P<article_slug>[\w-]+)/publish$", views.publish_view, name="publish_article"),
    url("(?P<article_slug>[\w-]+)/unpublish$", views.unpublish_view, name="unpublish_article"),
    url("(?P<article_slug>[\w-]+)/history$", views.article_history_view, name="article_history"),
    url("(?P<article_slug>[\w-]+)/edit$", views.edit_article_view, name="edit_article"),
    url("(?P<article_slug>[\w-]+)/r/(?P<revision_id>\d+)$", views.read_article_view, name="read_article_revision")
]
