from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

import markdown2

from .models import Tag, Article
from .forms import ArticleForm
from ..auth.decorators import superuser_required


def read_article_view(request, article_slug):
    """Read an article"""

    article = get_object_or_404(Article, slug=article_slug, publish_id__isnull=False)
    public_article = get_object_or_404(article.history, history_id=article.publish_id)
    return render(request, 'docs/read.html', {
        'title': public_article.title,
        'article': article,
        'content': markdown2.markdown(public_article.content, extras=[
            'fenced-code-blocks',
            'header-ids'
        ])
    })

@login_required
def index_view(request):
    """Home page for documentation"""

    tags = Tag.objects.filter(article__isnull=False).distinct()
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
            article.save(history=True)
            messages.success(request, 'Successfuly created document')
            return redirect('edit_article', article_slug=article.slug)
        messages.error(request, 'Invalid form')
        return render(request, 'docs/edit.html', {'form': form})

    tags = Tag.objects.all()
    form = ArticleForm()
    return render(request, 'docs/edit.html', {'form': form, 'tags': tags})

@login_required
@superuser_required
def edit_article_view(request, article_slug):
    """Edit preexisting article"""
    article = get_object_or_404(Article, slug=article_slug)
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
            if request.POST['submit'] == 'post':
                try:
                    article.publish_id = article.history.latest().history_id
                    article.save(history=True)
                    messages.success(request, 'Successfully published document :)')
                except:
                    messages.error(request, 'Failed to publish document')
            else:
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
