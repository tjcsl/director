from django.shortcuts import render, redirect
from django.contrib.auth import logout

from ..sites.models import Site

def index_view(request):
    if request.user.is_authenticated():
        return render(request, "dashboard.html", {
            "sites": Site.objects.filter(group__users__id=request.user.id).order_by("name")
        })
    else:
        return login_view(request)


def login_view(request):
    return render(request, "login.html", {})


def logout_view(request):
    logout(request)
    return redirect("index")
