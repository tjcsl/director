from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import UserForm
from ..authentication.decorators import superuser_required

from .models import User, Group

@login_required
def settings_view(request):
    context = {
        "groups": Group.objects.filter(users__id=request.user.id).order_by("name")
    }
    return render(request, "users/settings.html", context)


@superuser_required
def create_view(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
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
            messages.success(request, "User {} edited!".format(user.username))
            return redirect("user_management")
    else:
        form = UserForm(instance=user)

    context = {
        "form": form
    }
    return render(request, "users/create_user.html", context)


@superuser_required
def manage_view(request):
    context = {
        "users": User.objects.filter(service=False).order_by("username")
    }
    return render(request, "users/management.html", context)
