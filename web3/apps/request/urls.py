from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^$", views.request_view, name="request_site"),
    url(r"^approve$", views.approve_view, name="approve_site"),
    url(r"^admin$", views.approve_admin_view, name="admin_site")
]
