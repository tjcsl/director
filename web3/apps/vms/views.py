from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def list_view(request):
    return render(request, "vms/list.html")
