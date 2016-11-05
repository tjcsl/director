from __future__ import unicode_literals

from django.db import models
from django.core import validators
from django.contrib.auth.models import AbstractBaseUser

# Create your models here.


class User(AbstractBaseUser):
    id = models.PositiveIntegerField(primary_key=True, validators=[validators.MinValueValidator(1000)])
    username = models.CharField(max_length=32)
    superuser = models.BooleanField(default=False)
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['id', 'superuser']


class Group(models.Model):
    id = models.PositiveIntegerField(primary_key=True, validators=[validators.MinValueValidator(1000)])
    name = models.CharField(max_length=32)
    users = models.ManyToManyField(User, related_name='groups')
