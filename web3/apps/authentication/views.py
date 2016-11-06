from django.shortcuts import render, redirect
from django.contrib.auth import logout


def index_view(request):
    if request.user.is_authenticated():
        return render(request, "index.html", {})
    else:
        return login_view(request)


def login_view(request):
    return render(request, "login.html", {})


def logout_view(request):
    logout(request)
    return redirect("index")
