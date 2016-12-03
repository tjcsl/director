from django.conf.urls import url

from . import views

urlpatterns = [
    url("^list$", views.list_view, name="vm_list"),
    url("^create$", views.create_view, name="create_vm"),
    url("^(?P<vm_id>\d+)$", views.info_view, name="vm_info"),
    url("^(?P<vm_id>\d+)/delete$", views.delete_view, name="vm_delete")
]
