from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import Group

@login_required
def settings_view(request):
    context = {
        "groups": Group.objects.filter(users__id=request.user.id).order_by("name")
    }
    return render(request, "users/settings.html", context)
