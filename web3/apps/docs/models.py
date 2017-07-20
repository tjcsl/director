from django.db import models
from django.template.defaultfilters import slugify
from simple_history.models import HistoricalRecords

import markdown2

from ..helpers import ModelDiffMixin
from ..users.models import User


class Tag(models.Model):

    """Tag for article"""

    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Article(models.Model, ModelDiffMixin):

    """A piece of documentation"""

    title = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    tags = models.ManyToManyField(Tag)
    author = models.ManyToManyField(User)

    content = models.TextField()

    history = HistoricalRecords()
    publish_id = models.IntegerField(null=True, blank=True)

    @property
    def publish_date(self):
        return self.history.get(history_id=self.publish_id).history_date

    @property
    def html(self):
        return markdown2.markdown(self.content, extras=[
            'fenced-code-blocks',
            'header-ids'
        ])

    def save(self, history=False, *args, **kwargs):
        if not self.id:
            self.slug = slugify(self.title)
        if not self.id or history:
            super().save(*args, **kwargs)
        else:
            self.skip_history_when_saving = True
            try:
                super().save(*args, **kwargs)
            finally:
                del self.skip_history_when_saving
