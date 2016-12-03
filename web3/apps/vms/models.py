import uuid

from django.db import models

from ..users.models import User


class VirtualMachine(models.Model):
    name = models.CharField(max_length=36, unique=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    description = models.TextField(blank=True)
    users = models.ManyToManyField(User, related_name='vms')
