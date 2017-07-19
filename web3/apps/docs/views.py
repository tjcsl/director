import logging

from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Tag, Article
from .forms import ArticleForm
from ..auth.decorators import superuser_required


logger = logging.getLogger(__name__)

@login_required
def index_view(request):
    """Home page for documentation"""

    tags = Tag.objects.all()
    return render(request, 'docs/home.html', {'tags': tags})


@login_required
@superuser_required
def new_article_view(request):
    """Write a new document"""
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            tags = form.cleaned_data['tags']
            article = form.save(commit=True)
            for tag_name in tags.split(','):
                tag, created = Tag.objects.get_or_create(name=tag_name)
                article.tags.add(tag)
            article.save()
            messages.success(request, 'Successfuly created document')
            return render(request, 'docs/edit.html', {'form': form})
        messages.error(request, 'Invalid form')
        return render(request, 'docs/edit.html', {'form': form})

    tags = Tag.objects.all()
    form = ArticleForm()
    return render(request, 'docs/edit.html', {'form': form, 'tags': tags})

@login_required
@superuser_required
def edit_article_view(request, article_id):
    """Edit preexisting article"""
    article = get_object_or_404(Article, id=article_id)
    tags = Tag.objects.all()

    if request.method == 'POST':
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            tags = form.cleaned_data['tags']
            article = form.save(commit=True)
            article.tags.clear()
            for tag_name in tags.split(','):
                tag, created = Tag.objects.get_or_create(name=tag_name)
                article.tags.add(tag)
            article.save()
            tags = Tag.objects.all()
            messages.success(request, 'Successfuly saved document')
            return render(request, 'docs/edit.html', {
                'form': form,
                'tags': tags,
                'article_tags': article.tags.all()
            })
        messages.error(request, 'Invalid form')
        return render(request, 'docs/edit.html', {
            'form': form,
            'tags': tags,
            'article_tags': article.tags.all()
        })

    form = ArticleForm(instance=article)
    return render(request, 'docs/edit.html', {
        'form': form,
        'tags': tags,
        'article_tags': article.tags.all()
    })
