from __future__ import unicode_literals

import os

from django.conf import settings
from django.core import validators
from django.db import models

from ..users.models import User, Group


class Site(models.Model):
    name = models.CharField(max_length=32, unique=True)
    category = models.CharField(max_length=16, choices=(
        ("static", "Static"),
        ("php", "PHP"),
        ("dynamic", "Dynamic")
    ))
    purpose = models.CharField(max_length=16, choices=(
        ("legacy", "Legacy"),
        ("user", "User"),
        ("activity", "Activity"),
        ("other", "Other")
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
            return "/web/legacy/{}/".format(self.name)
        else:
            return "/web/{}/".format(self.name)


    @property
    def private_path(self):
        return os.path.join(self.path, "private")


    @property
    def public_path(self):
        return os.path.join(self.path, "public")


    @property
    def has_repo(self):
        return not settings.DEBUG and os.path.isdir(os.path.join(self.public_path, ".git"))

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
