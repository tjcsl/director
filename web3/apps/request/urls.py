from django.conf.urls import url

from . import views

urlpatterns = [
    url("^$", views.request_view, name="request_site"),
    url("^approve$", views.approve_view, name="approve_site"),
    url("^admin$", views.approve_admin_view, name="admin_site")
]
