from django.db import models

from ..users.models import User


class VirtualMachine(models.Model):
    name = models.CharField(max_length=32, unique=True)
    description = models.TextField(blank=True)

    users = models.ManyToManyField(User, related_name='vm_groups')
