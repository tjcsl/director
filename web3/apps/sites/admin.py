from django.contrib import admin

from .models import Database, DatabaseHost, Process, Site, SiteHost

# Register your models here.

admin.site.register(Site)
admin.site.register(SiteHost)
admin.site.register(Database)
admin.site.register(DatabaseHost)
admin.site.register(Process)
