from django.conf.urls import url

from .views import sites, databases, editor

urlpatterns = [
    url("^create$", sites.create_view, name="create_site"),
    url("^(?P<site_id>\d+)/$", sites.info_view, name="info_site"),
    url("^(?P<site_id>\d+)/edit$", sites.edit_view, name="edit_site"),
    url("^(?P<site_id>\d+)/delete$", sites.delete_view, name="delete_site"),

    # Site Editing
    url("^(?P<site_id>\d+)/terminal$", editor.web_terminal_view, name="web_terminal"),
    url("^(?P<site_id>\d+)/nginx/edit$", editor.edit_nginx_view, name="edit_nginx"),
    url("^(?P<site_id>\d+)/files$", editor.editor_view, name="editor"),
    url("^(?P<site_id>\d+)/files/path$", editor.editor_path_view, name="editor_path"),
    url("^(?P<site_id>\d+)/files/load$", editor.editor_load_view, name="editor_load"),
    url("^(?P<site_id>\d+)/files/save$", editor.editor_save_view, name="editor_save"),
    url("^(?P<site_id>\d+)/files/delete$", editor.editor_delete_view, name="editor_delete"),
    url("^(?P<site_id>\d+)/files/create$", editor.editor_create_view, name="editor_create"),
    url("^(?P<site_id>\d+)/files/download$", editor.editor_download_view, name="editor_download"),
    url("^(?P<site_id>\d+)/files/rename$", editor.editor_rename_view, name="editor_rename"),
    url("^(?P<site_id>\d+)/files/upload$", editor.editor_upload_view, name="editor_upload"),
    url("^(?P<site_id>\d+)/files/move$", editor.editor_move_view, name="editor_move"),
    url("^(?P<site_id>\d+)/files/process$", editor.editor_process_view, name="editor_process"),
    url("^(?P<site_id>\d+)/files/exec$", editor.editor_exec_view, name="editor_exec"),

    # Site Databases
    url("^(?P<site_id>\d+)/database/create$", databases.create_database_view, name="create_database"),
    url("^(?P<site_id>\d+)/database/edit$", databases.modify_database_view, name="edit_database"),
    url("^(?P<site_id>\d+)/database/edit/sql$", databases.sql_database_view, name="sql_database"),
    url("^(?P<site_id>\d+)/database/backup$", databases.backup_database_view, name="backup_database"),
    url("^(?P<site_id>\d+)/database/backup/dump$", databases.dump_database_view, name="dump_sql"),
    url("^(?P<site_id>\d+)/database/backup/load$", databases.load_database_view, name="load_sql"),
    url("^(?P<site_id>\d+)/database/delete$", databases.delete_database_view, name="delete_database"),
    url("^(?P<site_id>\d+)/database/regenenerate$", databases.regenerate_database_view, name="regenerate_database"),

    # VMs and Processes
    url("^(?P<site_id>\d+)/vm/edit$", sites.modify_vm_view, name="edit_vm"),
    url("^(?P<site_id>\d+)/process/edit$", sites.modify_process_view, name="edit_process"),
    url("^(?P<site_id>\d+)/process/restart$", sites.restart_process_view, name="restart_process"),
    url("^(?P<site_id>\d+)/process/delete$", sites.delete_process_view, name="delete_process"),

    # Actions and Integrations
    url("^(?P<site_id>\d+)/action/permission$", sites.permission_view, name="permission_site"),
    url("^(?P<site_id>\d+)/action/config$", sites.config_view, name="config_site"),
    url("^(?P<site_id>\d+)/action/generate_key$", sites.generate_key_view, name="generate_rsa_key"),
    url("^(?P<site_id>\d+)/action/git_pull$", sites.git_pull_view, name="git_pull"),
    url("^(?P<site_id>\d+)/action/git_setup$", sites.git_setup_view, name="github_automatic_setup"),
    url("^(?P<site_id>\d+)/action/git_path$", sites.set_git_path_view, name="set_git_path"),
    url("^(?P<site_id>\d+)/webhook$", sites.webhook_view, name="git_webhook")
]
