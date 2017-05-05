import requests
import json

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from .forms import UserForm
from .helpers import create_user, create_webdocs
from ..authentication.decorators import superuser_required
from ..sites.helpers import flush_permissions, write_new_index_file, reload_services
from ...utils.tjldap import get_full_name

from requests.utils import quote
from .models import User, Group
from ..sites.models import Site


@login_required
def settings_view(request):
    if request.method == "POST":
        email = request.POST.get("email", None)
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "You entered an invalid email address!")
            return redirect("user_settings")
        request.user.email = email
        request.user.save()
        messages.success(request, "Your email address has been updated!")
        return redirect("user_settings")

    github_info = get_github_info(request) if request.user.github_token else None
    context = {
        "groups": Group.objects.filter(users__id=request.user.id).order_by("name"),
        "github_username": github_info.get("login", None) if github_info else None
    }
    return render(request, "users/settings.html", context)


@superuser_required
def create_view(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            if not user.full_name:
                profile = request.user.api_request("profile/{}".format(user.username))
                user.full_name = profile.get("common_name", get_full_name(user.username))
                user.save()
            messages.success(request, "User {} created!".format(user.username))
            return redirect("user_management")
    else:
        form = UserForm()

    context = {
        "form": form
    }
    return render(request, "users/create_user.html", context)


@superuser_required
def edit_view(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()
            if not user.full_name:
                ldap_full_name = get_full_name(user.username)
                if ldap_full_name:
                    user.full_name = ldap_full_name
                else:
                    profile = request.user.api_request("profile/{}".format(user.username))
                    user.full_name = profile.get("common_name", "")
                user.save()
            messages.success(request, "User {} edited!".format(user.username))
            return redirect("user_management")
    else:
        form = UserForm(instance=user)

    context = {
        "form": form,
        "groups": user.unix_groups.all()
    }
    return render(request, "users/create_user.html", context)


@superuser_required
def manage_view(request):
    context = {
        "users": User.objects.filter(service=False).order_by("username")
    }
    return render(request, "users/management.html", context)


@login_required
def create_webdocs_view(request):
    if not request.user.is_staff:
        if request.user.has_webdocs:
            return redirect("info_site", site_id=Site.objects.get(name=request.user.username, purpose="user").id)
        if request.method == "POST":
            accepted = request.POST.get("agreement", False)

            if not accepted:
                messages.error(request, "You must accept the agreement to create a webdocs!")
                return redirect("create_webdocs")

            site = create_webdocs(request.user, purpose="user")
            write_new_index_file(site)
            messages.success(request, "Your webdocs has been created!")
            return redirect("info_site", site_id=site.id)

        return render(request, "users/create_webdocs.html", {"finished": False})

    if request.method == "POST":
        import_legacy = request.POST.get("legacy", False)
        no_users = request.POST.get("no-user", False)

        if import_legacy == "false":
            import_legacy = False

        if no_users == "false":
            no_users = False

        students = [x.strip() for x in request.POST.get("students", "").split("\n")]
        students = [x for x in students if x]

        success = []
        failure = []

        for username in students:
            if not no_users:
                user = create_user(request, username)
            if no_users or user:
                site = create_webdocs(username if no_users else user, batch=True, purpose=("legacy" if import_legacy else "user"))
                if site:
                    success.append(username)
                    continue
            failure.append(username)

        flush_permissions()
        reload_services()

        if request.GET.get("json", False) is not False:
            return JsonResponse({"success": success, "failure": failure})
        else:
            return render(request, "users/create_webdocs.html", {
                "finished": True,
                "success": success,
                "failure": failure
            })

    return render(request, "users/create_webdocs.html", {"finished": False})


@login_required
def github_link_view(request):
    return redirect("https://github.com/login/oauth/authorize?client_id={}&scope={}".format(settings.GITHUB_CLIENT_ID, "repo"))


@login_required
def github_unlink_view(request):
    u = request.user
    u.github_token = ""
    u.save()
    messages.success(request, "Your GitHub account has been unlinked!")
    return redirect("user_settings")


@csrf_exempt
@login_required
def github_oauth_view(request):
    code = request.GET.get("code", None)

    if not code:
        messages.error(request, "No code supplied with request!")
        return redirect("user_settings")

    r = requests.post("https://github.com/login/oauth/access_token", data={
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": code
    }, headers={"Accept": "application/json"})
    response = json.loads(r.text)
    request.user.github_token = response.get("access_token", "")
    request.user.save()

    messages.success(request, "Account linked with GitHub!")
    return redirect("user_settings")


def get_github_info(request):
    return request.user.github_api_request("/user")


@login_required
def teacher_lookup_view(request):
    name = request.GET.get("name", "")
    if not name:
        return JsonResponse({"teachers": []})
    responses = request.user.api_request("search/{}".format(quote(name)))
    return JsonResponse({
        "teachers": [{
            "username": x["username"],
            "name": x["full_name"]
        } for x in responses["results"] if x["user_type"] == "tjhsstTeacher"]
    })
