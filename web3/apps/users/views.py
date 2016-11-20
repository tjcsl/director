from django.shortcuts import render, redirect
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
def create_user_view(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "User {} created!".format(user.username))
            return redirect("index")
    else:
        form = UserForm()

    context = {
        "form": form
    }
    return render(request, "users/create_user.html", context)

@superuser_required
def manage_user_view(request):
    context = {
        "users": User.objects.filter(service=False).order_by("username")
    }
    return render(request, "users/management.html", context)
