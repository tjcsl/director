from django.conf.urls import url

from . import views

urlpatterns = [
    url("^settings$", views.settings_view, name="user_settings")
]
