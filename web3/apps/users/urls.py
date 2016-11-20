from django.conf.urls import url

from . import views

urlpatterns = [
    url("^settings$", views.settings_view, name="user_settings"),
    url("^create$", views.create_user_view, name="create_user"),
    url("^management$", views.manage_user_view, name="user_management")
]
