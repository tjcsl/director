import libvirt
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods

from .forms import VirtualMachineForm
from .helpers import call_api
from .models import VirtualMachine
from ..sites.helpers import add_access_token


@login_required
def list_view(request):
    """
    Render the main VM list
    """
    vm_list = VirtualMachine.objects.filter(Q(users=request.user) | Q(owner=request.user)).distinct().order_by("name")

    statuses = dict()
    for vm in vm_list:
        statuses[str(vm.uuid)] = vm.get_state()

    if request.user.is_superuser:
        su_vm_list = VirtualMachine.objects.exclude(Q(users=request.user) | Q(owner=request.user)).distinct().order_by(
            "name")
    else:
        su_vm_list = None

    return render(request, "vms/list.html", {"vm_list": vm_list, "su_vm_list": su_vm_list, "vm_status": statuses})


@login_required
def info_view(request, vm_id):
    vm = get_object_or_404(VirtualMachine, id=vm_id)

    is_owner = vm.owner == request.user or request.user.is_superuser

    if not vm.users.filter(id=request.user.id).exists() and not is_owner:
        raise PermissionDenied

    # vm_state = call_api("container.state", name=str(vm.uuid))
    if vm.is_online():
        vm_ips = vm.ips
    else:
        vm_ips = []

    return render(request, "vms/info.html", {"vm": vm, "vm_state": vm.get_state(), "vm_ips": vm_ips, "owner": is_owner})


@require_http_methods(["POST"])
@login_required
def start_view(request, vm_id):
    vm = get_object_or_404(VirtualMachine, id=vm_id)
    if not request.user.is_superuser and not vm.users.filter(
            id=request.user.id).exists() and not vm.owner == request.user:
        raise PermissionDenied

    try:
        vm.power_on()
        messages.success(request, "Virtual machine started!")
    except libvirt.libvirtError:
        messages.error(request, "Failed to start virtual machine!")

    return redirect("vm_info", vm_id=vm_id)


@require_http_methods(["POST"])
@login_required
def stop_view(request, vm_id):
    vm = get_object_or_404(VirtualMachine, id=vm_id)
    if not request.user.is_superuser and not vm.users.filter(
            id=request.user.id).exists() and not vm.owner == request.user:
        raise PermissionDenied

    try:
        vm.power_off()
        messages.success(request, "Virtual machine stopped!")
    except libvirt.libvirtError as e:
        messages.error(request, "Failed to stop virtual machine! ({})".format(e))

    return redirect("vm_info", vm_id=vm_id)


@require_http_methods(["POST"])
@login_required
def pause_view(request, vm_id):
    vm = get_object_or_404(VirtualMachine, id=vm_id)
    if not request.user.is_superuser and not vm.users.filter(
            id=request.user.id).exists() and not vm.owner == request.user:
        raise PermissionDenied

    try:
        vm.get_domain().suspend()
        messages.success(request, "Virtual machine paused.")
    except libvirt.libvirtError as e:
        messages.error(request, "Failed to pause virtual machine. ({})".format(e))

    return redirect("vm_info", vm_id=vm_id)


@require_http_methods(["POST"])
@login_required
def resume_view(request, vm_id):
    vm = get_object_or_404(VirtualMachine, id=vm_id)
    if not request.user.is_superuser and not vm.users.filter(
            id=request.user.id).exists() and not vm.owner == request.user:
        raise PermissionDenied

    try:
        vm.get_domain().resume()
        messages.success(request, "Virtual machine resumed.")
    except libvirt.libvirtError as e:
        messages.error(request, "Failed to resume virtual machine. ({})".format(e))

    return redirect("vm_info", vm_id=vm_id)


@login_required
def delete_view(request, vm_id):
    vm = get_object_or_404(VirtualMachine, id=vm_id)

    if not request.user.is_superuser and not vm.owner == request.user:
        raise PermissionDenied

    if request.method == "POST":
        if request.POST.get("confirm", None) == vm.name:
            try:
                vm.get_domain().destroy()
                vm.get_domain().undefine()
                vm.delete()
                messages.success(request, "Virtual machine deleted!")
            except libvirt.libvirtError:
                messages.error(request, "Failed to delete VM! ({})")
            return redirect("vm_list")
        else:
            messages.error(request, "Failed deletion confirmation!")

    return render(request, "vms/delete.html", {"vm": vm})


@login_required
def create_view(request):
    if request.method == "POST":
        current_vms = VirtualMachine.objects.filter(owner=request.user).count()
        if not request.user.is_superuser and not request.user.is_staff and current_vms >= settings.MAX_VMS:
            messages.error(request, "You can create a maximum of {} VMs! Contact a sysadmin if you need more.".format(
                settings.MAX_VMS))
            return redirect("vm_list")
        form = VirtualMachineForm(request.POST, user=request.user)
        if form.is_valid():
            instance = form.save()
            if instance:
                messages.success(request, "Virtual machine created!")
                return redirect("vm_info", vm_id=instance.id)
            else:
                messages.error(request, "Failed to create virtual machine!")
                return redirect("vm_list")
    else:
        form = VirtualMachineForm(user=request.user)
    return render(request, "vms/create.html", {"form": form, "vm": None})


@login_required
def edit_view(request, vm_id):
    vm = get_object_or_404(VirtualMachine, id=vm_id)

    if not request.user.is_superuser and not vm.owner == request.user:
        raise PermissionDenied

    if request.method == "POST":
        form = VirtualMachineForm(request.POST, user=request.user, instance=vm)
        if form.is_valid():
            vm = form.save()
            return redirect("vm_info", vm_id=vm.id)
    else:
        form = VirtualMachineForm(user=request.user, instance=vm)
    context = {
        "form": form,
        "vm": vm
    }
    return render(request, "vms/create.html", context)


@login_required
@add_access_token
def terminal_view(request, vm_id):
    vm = get_object_or_404(VirtualMachine, id=vm_id)

    if not request.user.is_superuser and not vm.users.filter(
            id=request.user.id).exists() and not vm.owner == request.user:
        raise PermissionDenied

    if not vm.is_online():
        messages.error(request, "VM is not online!")

    return render(request, "vms/web_terminal.html", {"vm": vm})
