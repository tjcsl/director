from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.conf import settings

from ..models import Site
from ..forms import SiteForm, ProcessForm
from ..helpers import (reload_services, update_supervisor, create_config_files, create_process_config, restart_supervisor,
                       get_supervisor_status, write_new_index_file, get_latest_commit, reload_nginx_config, list_executable_files)

from ...vms.models import VirtualMachine

from ....utils.emails import send_new_site_email


@login_required
def create_view(request):
    # Redirect the user if any approvals need to be done.
    if request.user.is_staff:
        if request.user.site_requests.filter(teacher_approval__isnull=True).exists():
            return redirect("approve_site")

    if request.method == "POST":
        form = SiteForm(request.POST, user=request.user)
        if form.is_valid():
            site = form.save()
            for user in site.group.users.filter(service=False):
                if not user == request.user:
                    send_new_site_email(user, site)
            if not site.category == "dynamic":
                write_new_index_file(site)
            reload_services()
            return redirect("info_site", site_id=site.id)
    else:
        form = SiteForm(user=request.user)

    context = {
        "form": form,
        "site": None,
        "project_domain": settings.PROJECT_DOMAIN
    }
    return render(request, "sites/create_site.html", context)


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
        "site": site,
        "project_domain": settings.PROJECT_DOMAIN
    }
    return render(request, "sites/create_site.html", context)


@login_required
def delete_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)

    if not request.user.is_superuser and not (site.purpose == "project" and site.group.users.filter(id=request.user.id).exists()):
        raise PermissionDenied

    if request.method == "POST":
        if not request.POST.get("confirm", None) == site.name:
            messages.error(request, "Delete confirmation failed!")
            return redirect("delete_site", site_id=site_id)
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
            site.process.delete()
            messages.success(request, "Process deleted!")
        except Site.process.RelatedObjectDoesNotExist:
            messages.error(request, "Process not found.")
        return redirect("info_site", site_id=site.id)
    else:
        return render(request, "sites/delete_process.html", {"site": site})


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
