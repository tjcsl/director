from django.conf.urls import url

from . import views

urlpatterns = [
    url("^settings$", views.settings_view, name="user_settings"),
    url("^github$", views.github_link_view, name="link_github"),
    url("^create$", views.create_view, name="create_user"),
    url("^edit/(?P<user_id>\d+)$", views.edit_view, name="edit_user"),
    url("^management$", views.manage_view, name="user_management")
]
