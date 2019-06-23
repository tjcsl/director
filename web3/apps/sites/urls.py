from django.conf.urls import url

from .views import sites, databases, editor, actions

urlpatterns = [
    url(r"^create$", sites.create_view, name="create_site"),
    url(r"^(?P<site_id>\d+)/$", sites.info_view, name="info_site"),
    url(r"^(?P<site_id>\d+)/edit$", sites.edit_view, name="edit_site"),
    url(r"^(?P<site_id>\d+)/delete$", sites.delete_view, name="delete_site"),

    # Site Editing
    url(r"^(?P<site_id>\d+)/terminal$", editor.web_terminal_view, name="web_terminal"),
    url(r"^(?P<site_id>\d+)/nginx/edit$", editor.edit_nginx_view, name="edit_nginx"),
    url(r"^(?P<site_id>\d+)/files$", editor.editor_view, name="editor"),
    url(r"^(?P<site_id>\d+)/files/path$", editor.editor_path_view, name="editor_path"),
    url(r"^(?P<site_id>\d+)/files/load$", editor.editor_load_view, name="editor_load"),
    url(r"^(?P<site_id>\d+)/files/save$", editor.editor_save_view, name="editor_save"),
    url(r"^(?P<site_id>\d+)/files/delete$", editor.editor_delete_view, name="editor_delete"),
    url(r"^(?P<site_id>\d+)/files/create$", editor.editor_create_view, name="editor_create"),
    url(r"^(?P<site_id>\d+)/files/download$", editor.editor_download_view, name="editor_download"),
    url(r"^(?P<site_id>\d+)/files/rename$", editor.editor_rename_view, name="editor_rename"),
    url(r"^(?P<site_id>\d+)/files/upload$", editor.editor_upload_view, name="editor_upload"),
    url(r"^(?P<site_id>\d+)/files/move$", editor.editor_move_view, name="editor_move"),
    url(r"^(?P<site_id>\d+)/files/process$", editor.editor_process_view, name="editor_process"),
    url(r"^(?P<site_id>\d+)/files/exec$", editor.editor_exec_view, name="editor_exec"),
    url(r"^(?P<site_id>\d+)/files/site_type$", editor.site_type_view, name="editor_site_type"),

    # Site Databases
    url(r"^(?P<site_id>\d+)/database/create$", databases.create_database_view, name="create_database"),
    url(r"^(?P<site_id>\d+)/database/edit$", databases.modify_database_view, name="edit_database"),
    url(r"^(?P<site_id>\d+)/database/edit/sql$", databases.sql_database_view, name="sql_database"),
    url(r"^(?P<site_id>\d+)/database/backup$", databases.backup_database_view, name="backup_database"),
    url(r"^(?P<site_id>\d+)/database/backup/dump$", databases.dump_database_view, name="dump_sql"),
    url(r"^(?P<site_id>\d+)/database/backup/load$", databases.load_database_view, name="load_sql"),
    url(r"^(?P<site_id>\d+)/database/delete$", databases.delete_database_view, name="delete_database"),
    url(r"^(?P<site_id>\d+)/database/regenenerate$", databases.regenerate_database_view, name="regenerate_database"),

    # VMs and Processes
    url(r"^(?P<site_id>\d+)/vm/edit$", sites.modify_vm_view, name="edit_vm"),
    url(r"^(?P<site_id>\d+)/process/edit$", sites.modify_process_view, name="edit_process"),
    url(r"^(?P<site_id>\d+)/process/status$", sites.process_status_view, name="process_status"),
    url(r"^(?P<site_id>\d+)/process/restart$", sites.restart_process_view, name="restart_process"),
    url(r"^(?P<site_id>\d+)/process/delete$", sites.delete_process_view, name="delete_process"),

    # Actions and Integrations
    url(r"^(?P<site_id>\d+)/action/permission$", actions.permission_view, name="permission_site"),
    url(r"^(?P<site_id>\d+)/action/config$", actions.config_view, name="config_site"),
    url(r"^(?P<site_id>\d+)/action/generate_key$", actions.generate_key_view, name="generate_rsa_key"),
    url(r"^(?P<site_id>\d+)/action/add_ssl$", actions.add_ssl_view, name="add_ssl"),
    url(r"^(?P<site_id>\d+)/action/git_pull$", actions.git_pull_view, name="git_pull"),
    url(r"^(?P<site_id>\d+)/action/git_setup$", actions.git_setup_view, name="github_automatic_setup"),
    url(r"^(?P<site_id>\d+)/action/git_path$", actions.set_git_path_view, name="set_git_path"),
    url(r"^(?P<site_id>\d+)/webhook$", actions.webhook_view, name="git_webhook"),

    # Installers
    url(r"^(?P<site_id>\d+)/install$", actions.install_options_view, name="install_options"),
    url(r"^(?P<site_id>\d+)/action/(?P<package>\w+)$", actions.install_package_view, name="install_package"),
]
