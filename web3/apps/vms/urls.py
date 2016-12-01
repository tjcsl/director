from django.conf.urls import url

from . import views

urlpatterns = [
    url("^list$", views.list_view, name="vm_list"),
]
