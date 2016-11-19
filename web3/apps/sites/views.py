from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required

from .models import Site
from .forms import CreateSiteForm
from .helpers import create_site_users, make_site_dirs, create_config_files, reload_services

@login_required
def create_view(request):
    if request.method == "POST":
        form = CreateSiteForm(request.POST)
        if form.is_valid():
            site = form.save(commit=False)
            user, group = create_site_users(site)
            if not settings.DEBUG:
                make_site_dirs(site)
                create_config_files(site)
                reload_services()
            group.users.add(request.user)
            return redirect("index")
    else:
        form = CreateSiteForm()

    context = {
        "form": form
    }
    return render(request, "sites/create_site.html", context)


