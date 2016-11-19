from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import Site
from .forms import CreateSiteForm

@login_required
def create_view(request):
    if request.method == "POST":
        form = CreateSiteForm(request.POST)
        if form.is_valid():
            # TODO: process form
            pass
    else:
        form = CreateSiteForm()

    context = {
        "form": form
    }
    return render(request, "sites/create_site.html", context)


