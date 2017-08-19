from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Article


admin.site.register(Article, SimpleHistoryAdmin)
