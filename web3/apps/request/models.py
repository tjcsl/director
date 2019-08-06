from django.db import models

from ..users.models import User


class SiteRequest(models.Model):
    """Represents a site request. The request is initiated by a student, approved by a teacher, and then processed by a sysadmin.

    Attributes:
        user
            The student that is requesting the site.
        teacher
            The teacher that will approve this request.
        request_date
            The date that the student submitted the request.
        teacher_approval
            Whether or not the teacher has approved the request.
        admin_approval
            Whether or not the administrator has processed the request.
        activity
            The activity that the site is intended for.
        extra_information
            Extra information about the request, such as additional software to be installed.

    """

    user = models.ForeignKey(User, related_name="requested_sites")
    teacher = models.ForeignKey(User, related_name="site_requests")

    request_date = models.DateTimeField(auto_now_add=True)

    teacher_approval = models.NullBooleanField(default=None)
    admin_approval = models.NullBooleanField(default=None)

    activity = models.CharField(max_length=32)
    extra_information = models.TextField(blank=True)
