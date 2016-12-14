from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.db.models import Count
from django.http import JsonResponse
from django.utils.crypto import get_random_string

from ..sites.models import Site
from ..users.models import User


import json


def index_view(request):
    if request.user.is_authenticated():
        return render(request, "dashboard.html", {
            "sites": Site.objects.annotate(num_users=Count("group__users")).filter(group__users=request.user).order_by("name"),
            "other_sites": Site.objects.exclude(group__users=request.user).annotate(num_users=Count("group__users")).order_by("name") if request.user.is_superuser else None
        })
    else:
        return login_view(request)


def about_view(request):
    return render(request, "about.html", {})


def login_view(request):
    request.user.access_token = get_random_string(64)
    return render(request, "login.html", {})


def logout_view(request):
    request.user.access_token = None
    request.user.save()
    logout(request)
    return redirect("index")


def node_auth_view(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body.decode("utf-8"))
            user = User.objects.get(id=body["uid"])
            site = Site.objects.get(id=body["sid"])
            if not user.is_superuser and not site.group.users.filter(id=user.id).exists():
                return JsonResponse({"granted": False, "error": "User does not have permission to access this website."}, status=403)
            if user.access_token != body["access_token"]:
                return JsonResponse({"granted": False, "error": "Invalid access token."})
            return JsonResponse({"granted": True, "site_homedir": site.path, "site_user": site.user.username})
        except Exception as e:
            return JsonResponse({"granted": False, "error": "Malformed request.", "exception": str(e)}, status=400)
    else:
        return JsonResponse({"error": "Method not allowed."}, status=405)
