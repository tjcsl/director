import os
import io
import shutil
import stat
import datetime
import zipfile
import mimetypes

from subprocess import Popen, PIPE

from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods

from .models import Site, Process
from .forms import SiteForm, ProcessForm, DatabaseForm
from .helpers import (reload_services, delete_site_files, create_config_files,
                      make_site_dirs, create_process_config, restart_supervisor,
                      get_supervisor_status, delete_process_config, write_new_index_file,
                      generate_ssh_key, run_as_site, do_git_pull, get_latest_commit,
                      fix_permissions, reload_nginx_config, check_nginx_config, demote,
                      list_executable_files)
from .database_helpers import delete_postgres_database, change_postgres_password, delete_mysql_database, change_mysql_password, list_tables

from ..authentication.decorators import superuser_required
from ..users.models import User
from ..vms.models import VirtualMachine
from ..request.models import SiteRequest

from ...utils.emails import send_new_site_email

from raven.contrib.django.raven_compat.models import client


@login_required
def create_view(request):
    if request.user.is_superuser:
        if request.method == "POST":
            form = SiteForm(request.POST, user=request.user)
            if form.is_valid():
                site = form.save()
                for user in site.group.users.filter(service=False):
                    send_new_site_email(user, site)
                if not site.category == "dynamic":
                    write_new_index_file(site)
                reload_services()
                return redirect("index")
        else:
            form = SiteForm(user=request.user)

        context = {
            "form": form
        }
        return render(request, "sites/create_site.html", context)
    else:
        if request.user.is_staff:
            if request.user.is_superuser and SiteRequest.objects.filter(teacher_approval=True, admin_approval=False).exists():
                return redirect("admin_site")
            if request.user.site_requests.filter(teacher_approval=False).exists():
                return redirect("approve_site")
            else:
                return render(request, "sites/create_info.html")
        else:
            return redirect("request_site")


@login_required
def edit_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    if request.method == "POST":
        current_members = list(site.group.users.filter(service=False).values_list('id', flat=True))
        form = SiteForm(request.POST, instance=site, user=request.user)
        if form.is_valid():
            site = form.save()
            for user in site.group.users.filter(service=False).exclude(id__in=current_members):
                send_new_site_email(user, site)
            reload_services()
            return redirect("info_site", site_id=site_id)
    else:
        form = SiteForm(instance=site, user=request.user)
    context = {
        "form": form
    }
    return render(request, "sites/create_site.html", context)


@login_required
def edit_nginx_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    nginx_path = "/etc/nginx/director.d/{}.conf".format(site.name)

    if os.path.isfile(nginx_path):
        with open(nginx_path, "r") as f:
            contents = f.read()
    else:
        contents = render_to_string("config/nginx.conf", {"site": site})

    if request.method == "POST":
        if not request.user.is_superuser:
            return JsonResponse({"error": "You are not allowed to make changes to this file!"})
        if not site.custom_nginx:
            return JsonResponse({"error": "You must enable custom nginx configuration before editing this file."})
        if request.POST.get("editor", None):
            with open(nginx_path, "w") as f:
                f.write(request.POST["editor"])
            if not check_nginx_config():
                with open(nginx_path, "w") as f:
                    f.write(contents)
                return JsonResponse({"error": "Invalid nginx configuration!"})
            else:
                reload_nginx_config()
                return JsonResponse({"success": "Nginx configuration updated!"})
        else:
            return JsonResponse({"error": "You must have a nginx configuration!"})
    else:
        return HttpResponse(contents, content_type="text/plain")


@superuser_required
def delete_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if request.method == "POST":
        if not request.POST.get("confirm", None) == site.name:
            messages.error(request, "Delete confirmation failed!")
            return redirect("delete_site", site_id=site_id)
        delete_site_files(site)
        reload_services()

        site.user.delete()
        site.group.delete()
        site.delete()
        messages.success(request, "Site {} deleted!".format(site.name))
        return redirect("index")
    context = {
        "site": site
    }
    return render(request, "sites/delete_site.html", context)


@login_required
def modify_process_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    if request.method == "POST":
        try:
            form = ProcessForm(request.user, request.POST, instance=site.process)
        except Site.process.RelatedObjectDoesNotExist:
            form = ProcessForm(request.user, request.POST, initial={"site": site.id})
        if form.is_valid():
            proc = form.save()
            create_process_config(proc)
            reload_services()
            messages.success(request, "Process modified!")
            return redirect("info_site", site_id=proc.site.id)
    else:
        try:
            form = ProcessForm(request.user, instance=site.process)
        except Site.process.RelatedObjectDoesNotExist:
            form = ProcessForm(request.user, initial={"site": site.id})
    context = {
        "form": form,
        "site": site,
        "files": list_executable_files(site.path, level=3)
    }
    return render(request, "sites/create_process.html", context)


@login_required
def modify_vm_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    if not site.category == "vm":
        messages.error(request, "Not a VM site!")
        return redirect("info_site", site_id=site.id)

    if request.method == "POST":
        vm = request.POST.get("vm", None)
        if hasattr(site, "virtual_machine"):
            current_vm = site.virtual_machine
            current_vm.site = None
            current_vm.save()
        if vm is not None and vm != "__blank__":
            vm = int(vm)
            new_vm = VirtualMachine.objects.get(id=vm)
            new_vm.site = site
            new_vm.save()

        create_config_files(site)
        reload_nginx_config()

        messages.success(request, "Virtual machine successfully linked!")
        return redirect("info_site", site_id=site.id)

    if request.user.is_superuser:
        vms = VirtualMachine.objects.all().order_by("name")
    else:
        vms = VirtualMachine.objects.filter(users=request.user).order_by("name")

    context = {
        "site": site,
        "vms": vms
    }
    return render(request, "sites/edit_vm.html", context)


@login_required
def create_database_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    if request.method == "POST":
        try:
            form = DatabaseForm(request.user, request.POST, instance=site.database)
        except Site.database.RelatedObjectDoesNotExist:
            form = DatabaseForm(request.user, request.POST, initial={"site": site.id})
        if form.is_valid():
            instance = form.save()
            if instance:
                messages.success(request, "New database created!")
            else:
                messages.error(request, "Failed to create database!")
            return redirect("info_site", site_id=site.id)
    else:
        try:
            form = DatabaseForm(request.user, instance=site.database)
        except:
            form = DatabaseForm(request.user, initial={"site": site.id})
    context = {
        "form": form,
        "site": site
    }
    return render(request, "sites/create_database.html", context)


@login_required
def modify_database_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    if not site.database:
        messages.error(request, "No database provisioned!")
        return redirect("info_site", site_id=site.id)

    return render(request, "sites/edit_database.html", {"site": site})


@login_required
def sql_database_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    if not site.database:
        return HttpResponse("ERROR: no database provisioned", content_type="text/plain")

    sql = request.POST.get("sql", "")
    version = request.POST.get("version", False) is not False

    if sql.startswith("\\!"):
        return HttpResponse("feature disabled\n\n", content_type="text/plain")

    if site.database.category == "mysql":
        if version:
            ret, out, err = run_as_site(site, ["mysql", "--version"])
        else:
            ret, out, err = run_as_site(site, ["mysql", "--user={}".format(site.database.username),
                                               "--host=mysql1", site.database.db_name, "-e", sql], env={"MYSQL_PWD": site.database.password})
    else:
        if version:
            ret, out, err = run_as_site(site, ["psql", "--version"])
        else:
            ret, out, err = run_as_site(site, ["psql", str(site.database), "-c", sql], env={"SHELL": "/usr/sbin/nologin"})
    return HttpResponse(out + err, content_type="text/plain")


@login_required
def backup_database_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    if not site.database:
        messages.error(request, "No database provisioned!")
        return redirect("info_site", site_id=site.id)

    return render(request, "sites/backup_database.html", {"site": site})


@login_required
def load_database_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    if request.method != "POST":
        return redirect("backup_database", site_id=site.id)

    if not site.database:
        messages.error(request, "No database provisioned!")
        return redirect("info_site", site_id=site.id)

    sql_file = request.FILES.get("file", None)
    if not sql_file:
        messages.error(request, "You must upload a .sql file!")
        return redirect("backup_database", site_id=site.id)

    if site.database.category == "postgresql":
        proc = Popen(["psql", str(site.database)], preexec_fn=demote(
            site.user.id, site.group.id), cwd=site.path, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    elif site.database.category == "mysql":
        proc = Popen(["mysql", "-u", site.database.username, "--password={}".format(site.database.password), "-h", "mysql1", site.database.db_name], preexec_fn=demote(
            site.user.id, site.group.id), cwd=site.path, stdin=PIPE, stdout=PIPE, stderr=PIPE)

    for chunk in sql_file.chunks():
        proc.stdin.write(chunk)

    out, err = proc.communicate()

    if proc.returncode == 0:
        messages.success(request, "Database import completed!")
    else:
        messages.error(request, "Database import failed!")
        client.captureMessage("Database import failed, ({}) - {} - {}".format(proc.returncode, out.decode("utf-8"), err.decode("utf-8")))

    return redirect("info_site", site_id=site.id)


@login_required
def dump_database_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    if request.method != "POST":
        return redirect("backup_database", site_id=site.id)

    if not site.database:
        messages.error(request, "No database provisioned!")
        return redirect("info_site", site_id=site.id)

    if site.database.category == "postgresql":
        # --cluster 9.6/main fixes the server version mismatch error
        ret, out, err = run_as_site(site, ["pg_dump", "--cluster", "9.6/main", str(site.database)], timeout=60)
    elif site.database.category == "mysql":
        ret, out, err = run_as_site(
            site, ["mysqldump", "-u", site.database.username, "--password={}".format(site.database.password), "-h", "mysql1", site.database.db_name], timeout=60)

    if ret == 0:
        resp = HttpResponse(out, content_type="application/force-download")
        resp["Content-Disposition"] = "attachment; filename=dump{}.sql".format(datetime.datetime.now().strftime("%m%d%Y"))
        return resp
    else:
        messages.error(request, "Failed to export database!")
        client.captureMessage("Database export failed, ({}) - {} - {}".format(ret, out, err))

    return redirect("info_site", site_id=site.id)


@login_required
def delete_database_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    if not site.database:
        messages.error(request, "No database provisioned!")
        return redirect("info_site", site_id=site.id)

    if request.method == "POST":
        if not request.POST.get("confirm", None) == site.name:
            messages.error(request, "Delete confirmation failed!")
            return redirect("delete_database", site_id=site_id)
        if site.database:
            flag = False
            if site.database.category == "postgresql":
                flag = delete_postgres_database(site.database)
            elif site.database.category == "mysql":
                flag = delete_mysql_database(site.database)
            if not flag:
                messages.error(request, "Failed to delete database!")
                return redirect("info_site", site_id=site.id)
            site.database.delete()
            create_config_files(site)
            messages.success(request, "Database deleted!")
        else:
            messages.error(request, "Database doesn't exist!")
        return redirect("info_site", site_id=site.id)
    else:
        return render(request, "sites/delete_database.html", {
            "site": site,
            "tables": list_tables(site.database)
        })


@require_http_methods(["POST"])
@login_required
def regenerate_database_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    site.database.password = User.objects.make_random_password(length=24)
    site.database.save()
    flag = True

    if site.database.category == "postgresql":
        flag = change_postgres_password(site.database)
    elif site.database.category == "mysql":
        flag = change_mysql_password(site.database)

    if flag:
        create_config_files(site)
        messages.success(request, "Database credentials regenerated!")
    else:
        messages.error(request, "Failed to regenerate database credentials!")
    return redirect("info_site", site_id=site.id)


@login_required
def delete_process_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    if request.method == "POST":
        try:
            delete_process_config(site.process)
            reload_services()
            site.process.delete()
            messages.success(request, "Process deleted!")
        except Site.process.RelatedObjectDoesNotExist:
            messages.error(request, "Process not found.")
        return redirect("info_site", site_id=site.id)
    else:
        return render(request, "sites/delete_process.html", {"site": site})


@login_required
def config_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    create_config_files(site)
    reload_services()

    messages.success(request, "Configuration files regenerated!")
    return redirect("info_site", site_id=site_id)


@login_required
def permission_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    make_site_dirs(site)
    fix_permissions(site)

    messages.success(request, "File permissions regenerated!")
    return redirect("info_site", site_id=site.id)


@login_required
def restart_process_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    restart_supervisor(site)

    messages.success(request, "Restarted supervisor application!")
    return redirect("info_site", site_id=site_id)


@login_required
def info_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    context = {
        "site": site,
        "users": site.group.users.filter(service=False).order_by("username"),
        "status": get_supervisor_status(site),
        "latest_commit": get_latest_commit(site),
        "webhook_url": request.build_absolute_uri(reverse("git_webhook", kwargs={"site_id": site_id})).replace("http://", "https://")
    }
    return render(request, "sites/info_site.html", context)


@require_http_methods(["POST"])
@login_required
def generate_key_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    generate_ssh_key(site)

    messages.success(request, "Generated new RSA public private key-pair!")
    return redirect(reverse("info_site", kwargs={"site_id": site_id}) + "#github-manual")


@login_required
def web_terminal_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    context = {
        "site": site
    }

    return render(request, "sites/web_terminal.html", context)


@login_required
def git_pull_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    output = do_git_pull(site)

    return JsonResponse({"ret": output[0], "out": output[1], "err": output[2]})


@csrf_exempt
def webhook_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if request.method == "POST":
        if not request.META["HTTP_USER_AGENT"].startswith("GitHub-Hookshot/"):
            return JsonResponse({"error": "Invalid user agent!"})
        if request.META["HTTP_X_GITHUB_EVENT"] == "ping":
            return JsonResponse({"success": True})
        if not request.META["HTTP_X_GITHUB_EVENT"] == "push":
            return JsonResponse({"error": "Only push events are supported at this time!"})
        output = do_git_pull(site)
        return JsonResponse({"success": bool(output[0] == 0)})
    else:
        return JsonResponse({"error": "Request method not allowed!"})


@require_http_methods(["POST"])
@login_required
def git_setup_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    if not request.user.github_token:
        messages.error(request, "You must connect your GitHub account first!")
    else:
        generate_ssh_key(site, overwrite=False)
        ret, out, err = run_as_site(site, "git remote -v", cwd=site.public_path)
        if ret != 0:
            messages.error(request, "Failed to detect the remote repository!")
        else:
            out = [[y for y in x.replace("\t", " ").split(" ") if y] for x in out.split("\n") if x]
            out = [x[1] for x in out if x[2] == "(fetch)"]
            out = [x for x in out if x.startswith("git@github.com") or x.startswith("https://github.com")]
            if not out:
                messages.error(request, "Did not find any remote repositories to pull from!")
            else:
                out = out[0]
                if out.startswith("git@github.com"):
                    out = out.split(":", 1)[1].rsplit(".", 1)[0]
                else:
                    a = out.rsplit("/", 2)
                    out = "{}/{}".format(a[-2], a[-1].rsplit(".", 1)[0])
                repo_info = request.user.github_api_request("/repos/{}".format(out))
                if repo_info is not None:
                    resp = request.user.github_api_request("/repos/{}/keys".format(out))
                    if resp is not None:
                        for i in resp:
                            if i["title"] == "Director" or i["key"].strip().split(" ")[1] == site.public_key.strip().split(" ")[1]:
                                request.user.github_api_request("/repos/{}/keys/{}".format(out, i["id"]), method="DELETE")
                        resp = request.user.github_api_request("/repos/{}/keys".format(out), method="POST", data={"title": "Director", "key": site.public_key.strip(), "read_only": True})
                        if resp:
                            resp = request.user.github_api_request("/repos/{}/hooks".format(out))
                            if resp:
                                webhook_url = request.build_absolute_uri(reverse("git_webhook", kwargs={"site_id": site_id})).replace("http://", "https://")
                                for i in resp:
                                    if i["config"]["url"] == webhook_url:
                                        break
                                else:
                                    request.user.github_api_request("/repos/{}/hooks".format(out), method="POST", data={
                                        "name": "web",
                                        "config": {
                                            "url": webhook_url,
                                            "content_type": "json"
                                        },
                                        "active": True
                                    })
                                messages.success(request, "The integration was set up!")
                            else:
                                messages.error(request, "Failed to retrieve repository webhooks!")
                        else:
                            messages.error(request, "Failed to add new deploy key!")
                    else:
                        if not repo_info["permissions"]["admin"]:
                            messages.error(request, "You do not have permission to add deploy keys. Ask the owner of the repository to set this integration up for you.")
                        else:
                            messages.error(request, "Failed to retrieve deploy keys!")
                else:
                    messages.error(request, "Failed to retrieve repository information from GitHub! Do you have access to this repository?")

    return redirect(reverse("info_site", kwargs={"site_id": site.id}) + "#github-automatic")


@login_required
def editor_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    context = {
        "site": site
    }

    return render(request, "sites/editor.html", context)


@login_required
def editor_path_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    requested_path = request.GET.get("path", "")
    path = os.path.abspath(os.path.join(site.path, requested_path))

    if not path.startswith(site.path) or not os.path.isdir(path):
        return JsonResponse({"error": "Invalid or nonexistent path!", "path": path})

    filesystem = []

    for f in os.listdir(path):
        fpath = os.path.join(path, f)
        fmode = os.lstat(fpath).st_mode
        if stat.S_ISDIR(fmode):
            obj = {"type": "d", "name": f}
        else:
            obj = {"type": "f", "name": f, "executable": fmode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)}
        if stat.S_ISLNK(fmode):
            obj["link"] = True
        filesystem.append(obj)

    return JsonResponse({"files": filesystem})


@login_required
def editor_load_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    requested_path = request.GET.get("name", "")
    path = os.path.abspath(os.path.join(site.path, requested_path))

    if not path.startswith(site.path) or not os.path.isfile(path):
        return JsonResponse({"error": "Invalid or nonexistent file!", "path": path})

    try:
        with open(path, "r") as f:
            contents = f.read()
    except UnicodeDecodeError:
        return JsonResponse({"error": "Editing binary files is not supported!"})
    except IOError:
        return JsonResponse({"error": "Failed to open file!"})

    return JsonResponse({"contents": contents})


@login_required
def editor_save_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    requested_path = request.GET.get("name", "")
    path = os.path.abspath(os.path.join(site.path, requested_path))

    if not path.startswith(site.path) or not os.path.isfile(path):
        return JsonResponse({"error": "Invalid or nonexistent file!", "path": path})

    with open(path, "w") as f:
        f.write(request.POST.get("contents"))

    return JsonResponse({"success": True})


@require_http_methods(["POST"])
@login_required
def editor_delete_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    requested_path = request.POST.getlist("name[]")
    path = [os.path.abspath(os.path.join(site.path, x)) for x in requested_path]

    if not all(x.startswith(site.path) for x in path) or not all(os.path.exists(x) for x in path):
        return JsonResponse({"error": "Invalid or nonexistent file or folder!", "path": path})

    for p in path:
        if os.path.isfile(p):
            os.remove(p)
        else:
            shutil.rmtree(p)

    return JsonResponse({"success": True})


@require_http_methods(["POST"])
@login_required
def editor_create_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    is_file = request.POST.get("type", "f") == "f"

    requested_path = request.POST.get("path", "")
    requested_new = os.path.basename(request.POST.get("name", ""))
    path = os.path.abspath(os.path.join(site.path, requested_path))

    if not path.startswith(site.path) or not os.path.isdir(path):
        return JsonResponse({"error": "Invalid or nonexistent folder!", "path": path})

    new_path = os.path.join(path, requested_new)

    if os.path.exists(new_path):
        return JsonResponse({"error": "The file or folder you are trying to create already exists!"})

    if is_file:
        open(new_path, "a").close()
    else:
        os.mkdir(new_path)

    os.lchown(new_path, site.user.id, site.group.id)

    return JsonResponse({"success": True})


@login_required
def editor_download_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    requested_path = request.GET.get("name", "")
    path = os.path.abspath(os.path.join(site.path, requested_path))

    if not path.startswith(site.path) or not os.path.exists(path):
        raise Http404

    if os.path.isfile(path):
        response = HttpResponse(content=open(path, "rb"))
        if request.GET.get("embed", False) is not False:
            response["Content-Type"] = mimetypes.guess_type(path)[0]
        else:
            response["Content-Type"] = "application/octet-stream"
            response["Content-Disposition"] = "attachment; filename={}".format(os.path.basename(path))
        return response
    else:
        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(path):
                for f in files:
                    filepath = os.path.join(root, f)
                    zipf.write(filepath, filepath[len(path):])
        response = HttpResponse(zip_io.getvalue())
        response["Content-Type"] = "application/x-zip-compressed"
        response["Content-Disposition"] = "attachment; filename={}.zip".format(os.path.basename(path))
        response["Content-Length"] = zip_io.tell()
        return response


@require_http_methods(["POST"])
@login_required
def editor_rename_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    new_name = os.path.basename(request.POST.get("newname", ""))
    requested_path = request.POST.get("name", "")
    path = os.path.abspath(os.path.join(site.path, requested_path))

    if not requested_path:
        return JsonResponse({"error": "You cannot rename the root directory!"})

    if not path.startswith(site.path) or not os.path.exists(path):
        return JsonResponse({"error": "Invalid or nonexistent file or folder!", "path": path})

    if not new_name:
        return JsonResponse({"error": "You must enter a valid name!", "path": path})

    os.rename(path, os.path.join(os.path.dirname(path), new_name))

    return JsonResponse({"success": True})


@require_http_methods(["POST"])
@login_required
def editor_upload_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    name = request.POST.get("path", "")
    path = os.path.abspath(os.path.join(site.path, name))

    if not path.startswith(site.path) or not os.path.isdir(path):
        return JsonResponse({"error": "Invalid or nonexistent folder!", "path": path})

    fs = request.FILES.getlist("file[]")

    if len(fs) == 0:
        return JsonResponse({"error": "No file(s) uploaded!"})

    for f in fs:
        filename = os.path.basename(f.name)
        with open(os.path.join(path, filename), "wb") as dest:
            for chunk in f.chunks():
                dest.write(chunk)

    fix_permissions(site)

    return JsonResponse({"success": True})


@require_http_methods(["POST"])
@login_required
def editor_move_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    old_path = request.POST.get("old", "")
    new_path = request.POST.get("new", "")
    old_path = os.path.abspath(os.path.join(site.path, old_path))
    new_path = os.path.abspath(os.path.join(site.path, new_path))

    if not old_path.startswith(site.path) or not os.path.exists(old_path):
        return JsonResponse({"error": "Invalid or nonexistent file or folder!", "path": old_path})

    if not new_path.startswith(site.path) or os.path.isfile(new_path):
        return JsonResponse({"error": "Invalid destination!", "path": new_path})

    os.rename(old_path, os.path.join(new_path, os.path.basename(old_path)))

    return JsonResponse({"success": True})


@require_http_methods(["POST"])
@login_required
def editor_process_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    path = request.POST.get("name", None)

    if not path:
        return JsonResponse({"error": "No file path received!"})

    path = os.path.abspath(os.path.join(site.path, path))

    if not path.startswith(site.path) or not os.path.isfile(path):
        return JsonResponse({"error": "Invalid or nonexistent file!"})

    if not os.access(path, os.X_OK):
        return JsonResponse({"error": "File not set as executable!"})

    if Process.objects.filter(site=site).exists():
        proc = Process.objects.get(site=site)
        proc.path = path
        proc.save()
    else:
        proc = Process.objects.create(site=site, path=path)

    create_process_config(proc)
    reload_services()

    return JsonResponse({"success": True})


@require_http_methods(["POST"])
@login_required
def editor_exec_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    path = request.POST.get("name", None)

    if not path:
        return JsonResponse({"error": "No file path received!"})

    path = os.path.abspath(os.path.join(site.path, path))

    if not path.startswith(site.path) or not os.path.isfile(path):
        return JsonResponse({"error": "Invalid or nonexistent file!"})

    st = os.stat(path)
    if not os.access(path, os.X_OK):
        os.chmod(path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    else:
        os.chmod(path, stat.S_IMODE(st.st_mode) & ~stat.S_IXUSR & ~stat.S_IXGRP & ~stat.S_IXOTH)

    return JsonResponse({"success": True})
