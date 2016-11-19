from __future__ import unicode_literals

from django.core import validators
from django.db import models

from ..users.models import User, Group


class Site(models.Model):
    name = models.CharField(max_length=32, unique=True)
    category = models.CharField(max_length=16, choices=(
        ("static", "static"),
        ("php", "php"),
        ("dynamic", "dynamic")
    ))
    purpose = models.CharField(max_length=16, choices=(
        ("legacy", "legacy"),
        ("user", "user"),
        ("activity", "activity"),
        ("other", "other")
    ))
    domain = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    user = models.OneToOneField(User)
    group = models.OneToOneField(Group)

    custom_nginx = models.BooleanField(default=False)

    @property
    def path(self):
        if self.purpose == "user":
            return "/web/user/{}/".format(self.name)
        elif self.purpose == "activity":
            return "/web/activities/{}/".format(self.name)
        elif self.purpose == "legacy":
            return "/web/legacy/{}".format(self.name)
        else:
            return "/web/{}/".format(self.name)

    def __str__(self):
        return self.name


class Process(models.Model):
    site = models.OneToOneField(Site)
    path = models.FilePathField(path="/web")

    def __str__(self):
        try:
            return self.site.name
        except:
            return "Unknown Site"
