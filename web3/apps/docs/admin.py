from simple_history.admin import SimpleHistoryAdmin

from django.contrib import admin

from .models import Article

admin.site.register(Article, SimpleHistoryAdmin)
