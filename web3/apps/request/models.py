from django.db import models

from ..users.models import User


class SiteRequest(models.Model):
    user = models.ForeignKey(User, related_name="requested_sites")
    teacher = models.ForeignKey(User, related_name="site_requests")

    request_date = models.DateTimeField(auto_now_add=True)

    teacher_approval = models.BooleanField(default=False)
    admin_approval = models.BooleanField(default=False)

    activity = models.CharField(max_length=32)
    extra_information = models.TextField(blank=True)
