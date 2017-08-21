# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings

from django.db import migrations
from urllib.parse import urlsplit


def forwards_func(apps, schema_editor):
    VirtualMachineHost = apps.get_model("vms", "VirtualMachineHost")
    VirtualMachine = apps.get_model("vms", "VirtualMachine")

    if hasattr(settings, "CONDUCTOR_AGENT_PATH") and settings.CONDUCTOR_AGENT_PATH:
        loc = urlsplit(settings.CONDUCTOR_AGENT_PATH)
    else:
        loc = None

    host, created = VirtualMachineHost.objects.get_or_create(
        hostname=loc.hostname if loc and loc.hostname else "conductor.tjhsst.edu"
    )

    for vm in VirtualMachine.objects.filter(host__isnull=True):
        vm.host = host
        vm.save()


def reverse_func(apps, schema_editor):
    VirtualMachine = apps.get_model("vms", "VirtualMachine")

    for vm in VirtualMachine.objects.filter(host__isnull=False):
        vm.host = None
        vm.save()


class Migration(migrations.Migration):
    dependencies = [
        ('vms', '0010_virtualmachine_host'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func)
    ]
