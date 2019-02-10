from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^$", views.list_view, name="vm_list"),
    url(r"^create$", views.create_view, name="create_vm"),
    url(r"^(?P<vm_id>\d+)$", views.info_view, name="vm_info"),
    url(r"^(?P<vm_id>\d+)/edit$", views.edit_view, name="vm_edit"),
    url(r"^(?P<vm_id>\d+)/terminal$", views.terminal_view, name="vm_terminal"),
    url(r"^(?P<vm_id>\d+)/delete$", views.delete_view, name="vm_delete"),
    url(r"^(?P<vm_id>\d+)/start$", views.start_view, name="start_vm"),
    url(r"^(?P<vm_id>\d+)/stop$", views.stop_view, name="stop_vm"),
    url(r"^(?P<vm_id>\d+)/password", views.password_view, name="set_vm_password")
]
