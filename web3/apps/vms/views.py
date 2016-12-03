from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..authentication.decorators import superuser_required

from .forms import VirtualMachineForm
from .models import VirtualMachine


@login_required
def list_view(request):
    return render(request, "vms/list.html")


@login_required
def info_view(request, vm_id):
    vm = get_object_or_404(VirtualMachine, id=vm_id)
    return render(request, "vms/info.html", {"vm": vm})


@superuser_required
def create_view(request):
    if request.method == "POST":
        form = VirtualMachineForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Virtual machine created!")
            return redirect("vm_list")
    else:
        form = VirtualMachineForm()
    return render(request, "vms/create_vm.html", {"form": form})
