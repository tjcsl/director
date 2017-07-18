from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import Tag
from .forms import ArticleForm
from ..auth.decorators import superuser_required

@login_required
def index_view(request):
    """Home page for documentation"""

    tags = Tag.objects.all()
    return render(request, 'docs/home.html', {'tags': tags})

@login_required
@superuser_required
def new_article_view(request):
    """Write a new document"""

    form = ArticleForm()
    return render(request, 'docs/edit.html', {'form': form})
