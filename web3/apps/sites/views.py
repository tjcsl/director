from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Site
from .forms import SiteForm
from .helpers import reload_services, delete_site_files, create_config_files, make_site_dirs

from ..authentication.decorators import superuser_required


@superuser_required
def create_view(request):
    if request.method == "POST":
        form = SiteForm(request.POST)
        if form.is_valid():
            site = form.save()
            if not settings.DEBUG:
                reload_services()
            return redirect("index")
    else:
        form = SiteForm()

    context = {
        "form": form
    }
    return render(request, "sites/create_site.html", context)


@superuser_required
def edit_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if request.method == "POST":
        form = SiteForm(request.POST, instance=site)
        if form.is_valid():
            site = form.save()
            if not settings.DEBUG:
                reload_services()
            return redirect("index")
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
def config_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied

    if not settings.DEBUG:
        create_config_files(site)
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
            for f in files + dirs:
                os.chown(os.path.join(root, f), site.user.id, site.group.id)

    messages.success(request, "File permissions regenerated!")
    return redirect("info_site", site_id=site_id)


@login_required
def info_view(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not request.user.is_superuser and not site.group.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    context = {
        "site": site,
        "users": site.group.users.filter(service=False).order_by("username")
    }
    return render(request, "sites/info_site.html", context)
