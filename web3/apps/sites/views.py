import os
import stat

from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string

from .models import Site
from .forms import SiteForm, ProcessForm, DatabaseForm
from .helpers import (reload_services, delete_site_files, create_config_files,
                      make_site_dirs, create_process_config, restart_supervisor,
                      get_supervisor_status, delete_process_config, write_new_index_file,
                      generate_ssh_key, run_as_site, delete_postgres_database, change_postgres_password,
                      do_git_pull, get_latest_commit, delete_mysql_database, change_mysql_password,
                      fix_permissions, reload_nginx_config, check_nginx_config, list_tables)

from ..authentication.decorators import superuser_required
from ..users.models import User

from ...utils.emails import send_new_site_email


@login_required
def create_view(request):
    if request.user.is_superuser:
        if request.method == "POST":
            form = SiteForm(request.POST, user=request.user)
            if form.is_valid():
                site = form.save()
                for user in site.group.users.filter(service=False):
                    send_new_site_email(user, site)
                if not settings.DEBUG:
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
        return render(request, "sites/create_info.html", {})


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
            if not settings.DEBUG:
                reload_services()
            return redirect("info_site", site_id=site_id)
    else:
        form = SiteForm(instance=site, user=request.user)
    context = {
        "form": form
    }
    return render(request, "sites/create_site.html", context)


@superuser_required
def edit_nginx_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    nginx_path = "/etc/nginx/director.d/{}.conf".format(site.name)

    if not settings.DEBUG and os.path.isfile(nginx_path):
        with open(nginx_path, "r") as f:
            contents = f.read()
    else:
        contents = render_to_string("config/nginx.conf", {"site": site})

    if request.method == "POST":
        if request.POST.get("editor", None):
            if not settings.DEBUG:
                with open(nginx_path, "w") as f:
                    f.write(request.POST["editor"])
                if not check_nginx_config():
                    with open(nginx_path, "w") as f:
                        f.write(contents)
                    messages.error(request, "Invalid nginx configuration!")
                else:
                    reload_nginx_config()
                    messages.success(request, "Nginx configuration updated!")
            else:
                messages.warning(request, "Not writing nginx config in debug mode!")
        else:
            messages.error(request, "You must have a nginx configuration!")
        return redirect("info_site", site_id=site_id)

    context = {
        "contents": contents,
        "site": site
    }
    return render(request, "sites/edit_nginx.html", context)


@superuser_required
def delete_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if request.method == "POST":
        if not request.POST.get("confirm", None) == site.name:
            messages.error(request, "Delete confirmation failed!")
            return redirect("info_site", site_id=site_id)
        if not settings.DEBUG:
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
            if not settings.DEBUG:
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
        "form": form
    }
    return render(request, "sites/create_process.html", context)


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
        "form": form
    }
    return render(request, "sites/create_database.html", context)


@login_required
def modify_database_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    return render(request, "sites/edit_database.html", {"site": site})


@login_required
def sql_database_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    if settings.DEBUG:
        return HttpResponse("WARNING: debug environment\n\n", content_type="text/plain")

    sql = request.POST.get("sql", "")
    version = request.POST.get("version", False) != False

    if site.database.category == "mysql":
        if version:
            ret, out, err = run_as_site(site, ["mysql", "--version"])
        else:
            ret, out, err = run_as_site(site, ["mysql", "--user={}".format(site.database.username), "--password={}".format(site.database.password), "--host=mysql1", site.database.db_name, "-e", sql])
    else:
        if version:
            ret, out, err = run_as_site(site, ["psql", "--version"])
        else:
            ret, out, err = run_as_site(site, ["psql", str(site.database), "-c", sql])
    return HttpResponse(out + err, content_type="text/plain")

@login_required
def delete_database_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    if request.method == "POST":
        if not request.POST.get("confirm", None) == site.name:
            messages.error(request, "Delete confirmation failed!")
            return redirect("info_site", site_id=site_id)
        if site.database:
            if not settings.DEBUG:
                flag = False
                if site.database.category == "postgresql":
                    flag = delete_postgres_database(site.database)
                elif site.database.category == "mysql":
                    flag = delete_mysql_database(site.database)
                if not flag:
                    messages.error(request, "Failed to delete database!")
                    return redirect("info_site", site_id=site.id)
            site.database.delete()
            messages.success(request, "Database deleted!")
        else:
            messages.error(request, "Database doesn't exist!")
        return redirect("info_site", site_id=site.id)
    else:
        return render(request, "sites/delete_database.html", {
            "site": site,
            "tables": list_tables(site.database) if not settings.DEBUG else None
        })


@login_required
def regenerate_database_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    site.database.password = User.objects.make_random_password(length=24)
    site.database.save()
    flag = True
    if not settings.DEBUG:
        if site.database.category == "postgresql":
            flag = change_postgres_password(site.database)
        elif site.database.category == "mysql":
            flag = change_mysql_password(site.database)
    if flag:
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
            if not settings.DEBUG:
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

    if not settings.DEBUG:
        create_config_files(site)
        if site.category is "dynamic" and Process.objects.filter(site=site).exists():
            create_process_config(Process.objects.get(site=site))
        reload_services()

    messages.success(request, "Configuration files regenerated!")
    return redirect("info_site", site_id=site_id)


@login_required
def permission_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    if not settings.DEBUG:
        make_site_dirs(site)
        fix_permissions(site)

    messages.success(request, "File permissions regenerated!")
    return redirect("info_site", site_id=site.id)


@login_required
def restart_process_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    if not settings.DEBUG:
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
        "status": get_supervisor_status(site) if not settings.DEBUG else None,
        "latest_commit": get_latest_commit(site) if site.has_repo else None,
        "webhook_url": request.build_absolute_uri(reverse("git_webhook", kwargs={"site_id": site_id})).replace("http://", "https://")
    }
    return render(request, "sites/info_site.html", context)


@login_required
def generate_key_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    if not settings.DEBUG:
        generate_ssh_key(site)

    messages.success(request, "Generated new RSA public private key-pair!")
    return redirect(reverse("info_site", kwargs={"site_id": site_id}) + "#github-integration")


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
