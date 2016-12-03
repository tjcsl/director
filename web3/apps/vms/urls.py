from django.conf.urls import url

from . import views

urlpatterns = [
    url("^list$", views.list_view, name="vm_list"),
    url("^create$", views.create_view, name="create_vm"),
    url("^(?P<vm_id>\d+)$", views.info_view, name="vm_info"),
    url("^(?P<vm_id>\d+)/edit$", views.edit_view, name="vm_edit"),
    url("^(?P<vm_id>\d+)/delete$", views.delete_view, name="vm_delete"),
    url("^(?P<vm_id>\d+)/start$", views.start_view, name="start_vm"),
    url("^(?P<vm_id>\d+)/stop$", views.stop_view, name="stop_vm"),
    url("^(?P<vm_id>\d+)/password", views.password_view, name="set_vm_password")
]
