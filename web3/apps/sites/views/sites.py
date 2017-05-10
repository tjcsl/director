import os

from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..models import Site
from ..forms import SiteForm, ProcessForm
from ..helpers import (reload_services, delete_site_files, create_config_files,
                       make_site_dirs, create_process_config, restart_supervisor,
                       get_supervisor_status, delete_process_config, write_new_index_file,
                       generate_ssh_key, run_as_site, do_git_pull, get_latest_commit,
                       fix_permissions, reload_nginx_config, list_executable_files, update_supervisor)

from ...authentication.decorators import superuser_required
from ...vms.models import VirtualMachine
from ...request.models import SiteRequest

from ....utils.emails import send_new_site_email


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
                return redirect("info_site", site_id=site.id)
        else:
            form = SiteForm(user=request.user)

        context = {
            "form": form,
            "site": None
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
        "form": form,
        "site": site
    }
    return render(request, "sites/create_site.html", context)


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
def process_status_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    return HttpResponse(get_supervisor_status(site))


@login_required
def modify_process_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    if site.category != "dynamic":
        messages.error(request, "You must set your site type to dynamic before adding a process.")
        return redirect("info_site", site_id=site_id)
    if request.method == "POST":
        try:
            form = ProcessForm(request.user, request.POST, instance=site.process)
        except Site.process.RelatedObjectDoesNotExist:
            form = ProcessForm(request.user, request.POST, initial={"site": site.id})
        if form.is_valid():
            proc = form.save()
            create_process_config(proc)
            update_supervisor()
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
def delete_process_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    if request.method == "POST":
        try:
            delete_process_config(site.process)
            update_supervisor()
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
def set_git_path_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    if request.method == "POST":
        path = request.POST.get("path", site.git_path)

        if not path.startswith(site.path) or not os.path.isdir(path):
            messages.error(request, "You entered a invalid or nonexistent path!")
            return redirect("set_git_path", site_id=site_id)

        site.repo_path = path
        site.save()

        messages.success(request, "The git repository path has been changed!")
        return redirect("info_site", site_id=site_id)

    return render(request, "sites/set_git_path.html", {"site": site})


@login_required
def git_pull_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    output = do_git_pull(site)

    return JsonResponse({"ret": output[0], "out": output[1], "err": output[2]})


@login_required
def install_wordpress_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    return render(request, "sites/install_wordpress.html", {"site": site})


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
        ret, out, err = run_as_site(site, "git remote -v", cwd=site.git_path)
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
