from django.db import models
from simple_history.models import HistoricalRecords

from ..users.models import User


class Tag(models.Model):

    """Tag for article"""

    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Article(models.Model):

    """A piece of documentation"""

    title = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    tags = models.ManyToManyField(Tag)
    author = models.ManyToManyField(User)

    content = models.TextField()

    published = models.BooleanField(default=False)
    history = HistoricalRecords()
    posted = models.DateField(db_index=True)
    edited = models.DateField(db_index=True, auto_now_add=True)
