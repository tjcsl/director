from django.db import models
from django.template.defaultfilters import slugify
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

    history = HistoricalRecords()
    posted = models.DateTimeField(db_index=True, null=True, blank=True)
    edited = models.DateTimeField(db_index=True, auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = slugify(self.title)
        super(Article, self).save(*args, **kwargs)
