from django.conf.urls import url

from . import views

urlpatterns = [
    url("^create$", views.create_view, name="create_site"),
    url("^ping$", views.ping_view, name="ping_site"),
    url("^(?P<site_id>\d+)/$", views.info_view, name="info_site"),
    url("^(?P<site_id>\d+)/edit$", views.edit_view, name="edit_site"),
    url("^(?P<site_id>\d+)/delete$", views.delete_view, name="delete_site"),

    # Site Editing
    url("^(?P<site_id>\d+)/terminal$", views.web_terminal_view, name="web_terminal"),
    url("^(?P<site_id>\d+)/nginx/edit$", views.edit_nginx_view, name="edit_nginx"),
    url("^(?P<site_id>\d+)/files$", views.editor_view, name="editor"),
    url("^(?P<site_id>\d+)/files/path$", views.editor_path_view, name="editor_path"),
    url("^(?P<site_id>\d+)/files/load$", views.editor_load_view, name="editor_load"),
    url("^(?P<site_id>\d+)/files/save$", views.editor_save_view, name="editor_save"),
    url("^(?P<site_id>\d+)/files/delete$", views.editor_delete_view, name="editor_delete"),

    # Site Databases
    url("^(?P<site_id>\d+)/database/create$", views.create_database_view, name="create_database"),
    url("^(?P<site_id>\d+)/database/edit$", views.modify_database_view, name="edit_database"),
    url("^(?P<site_id>\d+)/database/edit/sql$", views.sql_database_view, name="sql_database"),
    url("^(?P<site_id>\d+)/database/backup$", views.backup_database_view, name="backup_database"),
    url("^(?P<site_id>\d+)/database/backup/dump$", views.dump_database_view, name="dump_sql"),
    url("^(?P<site_id>\d+)/database/backup/load$", views.load_database_view, name="load_sql"),
    url("^(?P<site_id>\d+)/database/delete$", views.delete_database_view, name="delete_database"),
    url("^(?P<site_id>\d+)/database/regenenerate$", views.regenerate_database_view, name="regenerate_database"),

    # VMs and Processes
    url("^(?P<site_id>\d+)/vm/edit$", views.modify_vm_view, name="edit_vm"),
    url("^(?P<site_id>\d+)/process/edit$", views.modify_process_view, name="edit_process"),
    url("^(?P<site_id>\d+)/process/restart$", views.restart_process_view, name="restart_process"),
    url("^(?P<site_id>\d+)/process/delete$", views.delete_process_view, name="delete_process"),

    # Actions and Integrations
    url("^(?P<site_id>\d+)/action/permission$", views.permission_view, name="permission_site"),
    url("^(?P<site_id>\d+)/action/config$", views.config_view, name="config_site"),
    url("^(?P<site_id>\d+)/action/generate_key$", views.generate_key_view, name="generate_rsa_key"),
    url("^(?P<site_id>\d+)/action/git_pull$", views.git_pull_view, name="git_pull"),
    url("^(?P<site_id>\d+)/action/git_setup$", views.git_setup_view, name="github_automatic_setup"),
    url("^(?P<site_id>\d+)/webhook$", views.webhook_view, name="git_webhook")
]
