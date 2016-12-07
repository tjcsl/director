import uuid

from django.db import models

from ..users.models import User
from ..sites.models import Site

from .helpers import call_api


class VirtualMachine(models.Model):
    name = models.CharField(max_length=255, unique=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    description = models.TextField(blank=True)
    users = models.ManyToManyField(User, related_name='vms')
    password = models.TextField(blank=True)
    site = models.OneToOneField(Site, related_name="virtual_machine", blank=True, null=True)

    def ip_address(self):
        vm_state = call_api("container.state", name=str(self.uuid))
        if vm_state == 0:
            return call_api("container.ips", name=str(self.uuid))[1][0]
        else:
            return "127.0.0.1"
