from django.conf.urls import url

from . import views

urlpatterns = [
    url("^$", views.manage_view, name="user_management"),
    url("^settings$", views.settings_view, name="user_settings"),
    url("^github/link$", views.github_link_view, name="link_github"),
    url("^github/unlink$", views.github_unlink_view, name="unlink_github"),
    url("^create$", views.create_view, name="create_user"),
    url("^edit/(?P<user_id>\d+)$", views.edit_view, name="edit_user"),
    url("^webdocs$", views.create_webdocs_view, name="create_webdocs"),
    url("^lookup$", views.teacher_lookup_view, name="teacher_lookup")
]
