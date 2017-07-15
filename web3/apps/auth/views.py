from django.shortcuts import render, redirect
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.signals import user_logged_in
from django.conf import settings
from django.contrib import messages

from ..sites.models import Site
from ..vms.models import VirtualMachine
from ..users.models import User
from ..sites.helpers import get_supervisor_statuses

from raven.contrib.django.raven_compat.models import client

import hashlib
import datetime


def index_view(request):
    if request.user.is_authenticated():
        sites = Site.objects.annotate(num_users=Count("group__users")).filter(group__users=request.user).order_by("name")

        if sites.count() == 0:
            return redirect("start")

        statuses = get_supervisor_statuses(list(sites.filter(category="dynamic").values_list("name", flat=True)))

        if request.user.is_superuser and request.GET.get("all", False):
            other_sites = Site.objects.exclude(group__users=request.user).annotate(num_users=Count("group__users")).order_by("name")
            other_statuses = get_supervisor_statuses(list(other_sites.filter(category="dynamic").values_list("name", flat=True)))
        else:
            other_sites = None
            other_statuses = None

        return render(request, "dashboard.html", {
            "sites": sites,
            "other_sites": other_sites,
            "statuses": statuses,
            "other_statuses": other_statuses
        })
    else:
        return login_view(request)


def about_view(request):
    return render(request, "about.html")


def guide_view(request):
    context = {
        'project_domain': settings.PROJECT_DOMAIN
    }

    return render(request, "guide.html", context)


def start_view(request):
    return render(request, "start.html")


def login_view(request):
    if settings.PASSWORD_AUTH and request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
        else:
            messages.error(request, "Incorrect username or password!")

        return redirect("index")

    context = {
        "password_auth": settings.PASSWORD_AUTH
    }

    return render(request, "login.html", context)


def grant_access_token(sender, user, request, **kwargs):
    request.user.access_token = get_random_string(24)
    request.user.save()


user_logged_in.connect(grant_access_token)


def logout_view(request):
    if request.user.is_authenticated():
        request.user.access_token = None
        request.user.save()
    logout(request)
    return redirect("index")


@csrf_exempt
def node_auth_view(request):
    """Provides authentication for the Node.js server."""
    if request.method == "POST":
        try:
            if not request.POST.get("uid", None):
                return JsonResponse({"granted": False, "error": "No user id sent to server!"})

            user = User.objects.get(id=int(request.POST.get("uid")))
            siteid = request.POST.get("sid", None)
            vmid = request.POST.get("vmid", None)

            if user.access_token != request.POST.get("access_token"):
                return JsonResponse({"granted": False, "error": "Invalid access token."})

            if siteid is not None and siteid != "":
                site = Site.objects.get(id=int(siteid))
                if not user.is_superuser and not site.group.users.filter(id=user.id).exists():
                    return JsonResponse({"granted": False, "error": "User does not have permission to access this website."}, status=403)
                return JsonResponse({
                    "granted": True,
                    "site": {
                        "id": site.id,
                        "name": site.name,
                        "homedir": site.path,
                        "purpose": site.purpose,
                        "user": site.user.username
                    },
                    "userid": user.id,
                    "user": user.username
                })

            if vmid is not None and vmid != "":
                vm = VirtualMachine.objects.get(id=int(vmid))
                if not user.is_superuser and not vm.owner == user and not vm.users.filter(id=user.id).exists():
                    return JsonResponse({"granted": False, "error": "User does not have permission to access this virtual machine."}, status=403)
                if not vm.ip_address or not vm.password:
                    return JsonResponse({"granted": False, "error": "No IP address or root password set!"})
                return JsonResponse({
                    "granted": True,
                    "vm": {
                        "id": vm.id,
                        "ip": vm.ip_address,
                        "password": vm.password
                    },
                    "userid": user.id,
                    "user": user.username
                })

        except Exception as e:
            client.captureException()
            return JsonResponse({"granted": False, "error": "Malformed request.", "exception": str(e)}, status=400)
    else:
        return JsonResponse({"error": "Method not allowed."}, status=405)


@login_required
def set_access_cookie_view(request):
    """Check if a user can view a .secure folder, and set a cookie if they can."""
    if "site" not in request.GET:
        messages.error(request, "No site specified!")
        return redirect("index")
    try:
        site = Site.objects.get(name=request.GET.get("site"))
    except Site.DoesNotExist:
        messages.error(request, "Invalid site!")
        return redirect("index")
    if not request.user.is_staff and not site.group.users.filter(id=request.user.id).exists():
        messages.error(request, "You do not have permissions to view this site!")
        return redirect("index")
    response = HttpResponseRedirect(request.GET.get("next", "/"))
    response.set_cookie("site_{}".format(site.name), cookie_value(request.user.username, site.name), domain=".tjhsst.edu", httponly=True)
    return response


def check_access_cookie_view(request):
    """Checks if a user has the cookie set that will allow them to view the .secure folder."""
    site_name = request.META.get("HTTP_DIRECTOR_SITE_NAME")
    site_cookie = request.COOKIES.get("site_{}".format(site_name))
    if not site_cookie:
        return HttpResponse("Unauthorized", status=401)
    if not len(site_cookie.split("_")) == 2:
        return HttpResponse("Invalid Cookie", status=401)
    username = site_cookie.split("_")[0]
    if not site_cookie == cookie_value(username, site_name):
        return HttpResponse("Invalid Cookie", status=401)
    return HttpResponse("Authorized", status=200)


def cookie_value(username, site_name):
    today = datetime.datetime.now().date()
    hashval = "{}{}{}{}{}{}".format(settings.COOKIE_SECRET, username, today.year, today.month, today.day, site_name)
    hashed = hashlib.sha256(hashval.encode()).hexdigest()
    return "{}_{}".format(username, hashed)
