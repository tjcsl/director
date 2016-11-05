from __future__ import unicode_literals

from django.core import validators
from django.db import models

from ..users.models import User, Group


class Site(models.Model):
    id = models.PositiveIntegerField(primary_key=True, validators=[validators.MinValueValidator(1000)])
    name = models.CharField(max_length=32, unique=True)
    category = models.CharField(max_length=16, choices=(
        ("legacy", "legacy"),
        ("static", "static"),
        ("php", "php"),
        ("dynamic", "dynamic")
    ))
    purpose = models.CharField(max_length=16, choices=(
        ("user", "user"),
        ("activity", "activity")
    ))
    domain = models.TextField()
    description = models.TextField()

    user = models.ForeignKey(User)
    group = models.ForeignKey(Group)

    @property
    def path(self):
        if self.purpose == "user":
            return "/web/user/{}/".format(self.name)
        elif self.purpose == "activity":
            return "/web/activities/{}/".format(self.name)
        else:
            return "/web/{}/".format(self.name)
