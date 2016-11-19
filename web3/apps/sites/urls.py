from django.conf.urls import url

from . import views

urlpatterns = [
    url("^create$", views.create_view, name="create_site"),
    url("^info/(?P<site_id>\d+)$", views.info_view, name="info_site"),
    url("^edit/(?P<site_id>\d+)$", views.edit_view, name="edit_site"),
    url("^delete/(?P<site_id>\d+)$", views.delete_view, name="delete_site")
]
