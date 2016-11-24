from django.conf.urls import url

from . import views

urlpatterns = [
    url("^create$", views.create_view, name="create_site"),
    url("^(?P<site_id>\d+)/info$", views.info_view, name="info_site"),
    url("^(?P<site_id>\d+)/edit$", views.edit_view, name="edit_site"),
    url("^(?P<site_id>\d+)/delete$", views.delete_view, name="delete_site"),
    url("^(?P<site_id>\d+)/process/edit$", views.modify_process_view, name="edit_process"),
    url("^(?P<site_id>\d+)/process/restart$", views.restart_process_view, name="restart_process"),
    url("^(?P<site_id>\d+)/process/delete$", views.delete_process_view, name="delete_process"),
    url("^(?P<site_id>\d+)/action/permission$", views.permission_view, name="permission_site"),
    url("^(?P<site_id>\d+)/action/config$", views.config_view, name="config_site"),
    url("^(?P<site_id>\d+)/action/generate_key$", views.generate_key_view, name="generate_rsa_key"),
    url("^(?P<site_id>\d+)/action/git_pull$", views.git_pull_view, name="git_pull"),
    url("^(?P<site_id>\d+)/webhook$", views.webhook_view, name="git_webhook")
]
