import os
import stat

from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .models import Site
from .forms import SiteForm, ProcessForm
from .helpers import (reload_services, delete_site_files, create_config_files,
                      make_site_dirs, create_process_config, restart_supervisor,
                      get_supervisor_status, delete_process_config, write_new_index_file,
                      generate_ssh_key, run_as_site)

from ..authentication.decorators import superuser_required

from ...utils.emails import send_new_site_email


@login_required
def create_view(request):
    if request.user.is_superuser:
        if request.method == "POST":
            form = SiteForm(request.POST)
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
            form = SiteForm()

        context = {
            "form": form
        }
        return render(request, "sites/create_site.html", context)
    else:
        return render(request, "sites/create_info.html", {})


@superuser_required
def edit_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if request.method == "POST":
        current_members = list(site.group.users.filter(service=False).values_list('id', flat=True))
        form = SiteForm(request.POST, instance=site)
        if form.is_valid():
            site = form.save()
            for user in site.group.users.filter(service=False).exclude(id__in=current_members):
                send_new_site_email(user, site)
            if not settings.DEBUG:
                reload_services()
            return redirect("info_site", site_id=site_id)
    else:
        form = SiteForm(instance=site)
    context = {
        "form": form
    }
    return render(request, "sites/create_site.html", context)


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
            form = ProcessForm(request.POST, instance=site.process)
        except Site.process.RelatedObjectDoesNotExist:
            form = ProcessForm(request.POST, initial={"site": site.id})
        if form.is_valid():
            proc = form.save()
            if not settings.DEBUG:
                create_process_config(proc)
                reload_services()
            messages.success(request, "Process modified!")
            return redirect("info_site", site_id=proc.site.id)
    else:
        try:
            form = ProcessForm(instance=site.process)
        except Site.process.RelatedObjectDoesNotExist:
            form = ProcessForm(initial={"site": site.id})
    context = {
        "form": form
    }
    return render(request, "sites/create_process.html", context)


@login_required
def delete_process_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    if request.method == "POST":
        try:
            site.process.delete()
            if not settings.DEBUG:
                delete_process_config(site)
                reload_services()
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
        for root, dirs, files in os.walk(site.path):
            dirs[:] = [d for d in dirs if not d == ".ssh"]
            for f in files + dirs:
                path = os.path.join(root, f)
                st = os.stat(path)
                os.chown(path, site.user.id, site.group.id)
                if stat.S_ISDIR(st.st_mode):
                    os.chmod(path, st.st_mode | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP)
                else:
                    os.chmod(path, st.st_mode | stat.S_IRGRP | stat.S_IWGRP)

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
        "webhook_url": request.build_absolute_uri(reverse("git_webhook", kwargs={"site_id": site_id}))
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
    return redirect("info_site", site_id=site_id)


def do_git_pull(site):
    if not settings.DEBUG:
        output = run_as_site(site, "git pull", cwd=site.public_path, env={
            "GIT_SSH_COMMAND": "ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i {}".format(os.path.join(site.private_path, ".ssh/id_rsa")),
            "HOME": site.private_path
        })
    else:
        output = (0, None, None)
    return output


@login_required
def git_pull_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    output = do_git_pull(site)

    return JsonResponse({"ret": output[0], "out": output[1], "err": output[2]})


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
