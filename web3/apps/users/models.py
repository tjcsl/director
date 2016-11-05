from __future__ import unicode_literals

from django.db import models
from django.core import validators
from django.contrib.auth.models import AbstractBaseUser

# Create your models here.


class User(AbstractBaseUser):
    uid = models.PositiveIntegerField(validators=[validators.MinValueValidator(1000)])
    gid = models.PositiveIntegerField(validators=[validators.MinValueValidator(1000)])
    username = models.CharField(max_length=32)
    superuser = models.BooleanField(default=False)
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['uid, gid', 'superuser']


class Group(models.Model):
    gid = models.PositiveIntegerField(primary_key=True, validators=[validators.MinValueValidator(1000)])
    groupname = models.CharField(max_length=32)
    users = models.ManyToManyField(User, related_name='groups')
