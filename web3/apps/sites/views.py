from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import Site
from .forms import CreateSiteForm

@login_required
def create_view(request):
    form = CreateSiteForm()
    context = {
        "form": form
    }
    return render(request, "sites/create_site.html", context)


