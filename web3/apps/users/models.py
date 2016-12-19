from __future__ import unicode_literals

from django.db import models
from django.core import validators
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager as DjangoUserManager
from django.utils import timezone

from social.apps.django_app.utils import load_strategy

import json
import requests

from raven.contrib.django.raven_compat.models import client


class UserManager(DjangoUserManager):
    pass


class User(AbstractBaseUser, PermissionsMixin):
    id = models.PositiveIntegerField(primary_key=True, validators=[validators.MinValueValidator(1000)])
    service = models.BooleanField(default=False)
    username = models.CharField(unique=True, max_length=32)
    full_name = models.CharField(max_length=60)
    email = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    github_token = models.CharField(max_length=40, blank=True)
    access_token = models.CharField(max_length=64, blank=True, null=True)
    USERNAME_FIELD = 'username'

    objects = UserManager()

    @property
    def has_webdocs(self):
        from ..sites.models import Site
        return Site.objects.filter(name=self.username, purpose="user").count() > 0

    @property
    def short_name(self):
        return self.username

    def get_short_name(self):
        return self.username

    def get_full_name(self):
        return self.full_name

    def get_social_auth(self):
        return self.social_auth.get(provider='ion')

    def api_request(self, url, params={}, refresh=True):
        s = self.get_social_auth()
        params.update({"format": "json"})
        params.update({"access_token": s.access_token})
        r = requests.get("https://ion.tjhsst.edu/api/{}".format(url), params=params)
        if r.status_code == 401:
            if refresh:
                self.get_social_auth().refresh_token(load_strategy())
                return self.api_request(url, params, False)
            else:
                client.captureMessage("Ion API Request Failure: {} {}".format(r.status_code, r.json()))
        return r.json()

    def github_api_request(self, url, method="GET", data={}):
        resp = requests.request(url="https://api.github.com{}".format(url),
                                headers={"Authorization": "token {}".format(self.github_token)}, method=method, json=data)
        if resp.status_code == 204:
            return True
        if resp.status_code == 404:
            return None
        if resp.status_code != 200 and resp.status_code != 201:
            if resp.status_code == 401:
                self.github_token = ""
                self.save()
            else:
                client.captureMessage("GitHub API Request Failure: {} {}\n{} {}\n".format(resp.status_code, resp.text, method, data))
                return None
        return json.loads(resp.text)


class Group(models.Model):
    id = models.PositiveIntegerField(primary_key=True, validators=[validators.MinValueValidator(1000)])
    service = models.BooleanField(default=False)
    name = models.CharField(max_length=32)
    users = models.ManyToManyField(User, related_name='unix_groups')

    def __str__(self):
        return self.name
