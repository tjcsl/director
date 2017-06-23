from django.contrib import admin

from .models import Site, Process, Database
# Register your models here.

admin.site.register(Site)
admin.site.register(Database)
admin.site.register(Process)
