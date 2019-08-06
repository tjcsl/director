from django.contrib import admin

from .models import VirtualMachine, VirtualMachineHost

# Register your models here.

admin.site.register(VirtualMachine)
admin.site.register(VirtualMachineHost)
