import uuid

from django.db import models
from django.utils.text import slugify

from ..users.models import User
from ..sites.models import Site

from .helpers import call_api

from django.core.cache import cache


class VirtualMachine(models.Model):
    name = models.CharField(max_length=255, unique=True)
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
        return ips[0] if len(ips) else None

    @property
    def hostname(self):
        return slugify(self.name).replace("_", "-")

    def __str__(self):
        return self.name
