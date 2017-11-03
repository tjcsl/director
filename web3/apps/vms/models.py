import uuid

from django.db import models
from django.utils.text import slugify

from ..users.models import User
from ..sites.models import Site

from .helpers import call_api

from django.core.cache import cache


class VirtualMachineHost(models.Model):
    """Represents a host for virtual machines.

    Attributes:
        hostname
            The host to connect to (ex: conductor.tjhsst.edu).
    """
    hostname = models.CharField(max_length=255)

    def __str__(self):
        return self.hostname


class VirtualMachine(models.Model):
    """Represents a virtual machine.

    Attributes:
        name
            The name of this virtual machine. The slugified version of this field is the host name of the machine.
        uuid
            The UUID of this virtual machine. Used by the API to identify virtual machines.
        description
            A description for the purpose of this virtual machine.
        owner
            The owner of this virtual machine. The owner can delete the machine and add other members.
        users
            The other users that have access to the virtual machine.
        password
            The password for the root account on the virtual machine.
        site
            If this field is set, the site proxies all requests to the virtual machine.
    """
    name = models.CharField(max_length=255, unique=True)
    host = models.ForeignKey(VirtualMachineHost)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, null=True)
    users = models.ManyToManyField(User, related_name='vms')
    password = models.TextField(blank=True)
    site = models.OneToOneField(Site, related_name="virtual_machine", blank=True, null=True)

    @property
    def ips(self):
        key = "vm:ip:{}".format(self.id)
        obj = cache.get(key)
        if obj:
            return obj
        else:
            vm_ips = call_api("container.ips", name=str(self.uuid))[1]
            cache.set(key, vm_ips)
        return vm_ips

    @property
    def ip_address(self):
        ips = self.ips
        return ips[-1] if len(ips) else None

    @property
    def hostname(self):
        return slugify(self.name).replace("_", "-")

    def __str__(self):
        return self.name
