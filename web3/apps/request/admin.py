from django.contrib import admin

from .models import SiteRequest


class SiteRequestAdmin(admin.ModelAdmin):
    list_display = ("activity", "user", "teacher", "request_date")
    ordering = ("admin_approval", "teacher_approval", "-request_date")
    raw_id_fields = ("user", "teacher")


admin.site.register(SiteRequest, SiteRequestAdmin)
