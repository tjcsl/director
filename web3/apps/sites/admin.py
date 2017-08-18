from django.contrib import admin

from .models import Site, Process, Database, DatabaseHost
# Register your models here.

admin.site.register(Site)
admin.site.register(Database)
admin.site.register(DatabaseHost)
admin.site.register(Process)
