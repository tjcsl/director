from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^$", views.manage_view, name="user_management"),
    url(r"^settings$", views.settings_view, name="user_settings"),
    url(r"^github/link$", views.github_link_view, name="link_github"),
    url(r"^github/unlink$", views.github_unlink_view, name="unlink_github"),
    url(r"^create$", views.create_view, name="create_user"),
    url(r"^edit/(?P<user_id>\d+)$", views.edit_view, name="edit_user"),
    url(r"^webdocs$", views.create_webdocs_view, name="create_webdocs"),
    url(r"^lookup$", views.teacher_lookup_view, name="teacher_lookup")
]
