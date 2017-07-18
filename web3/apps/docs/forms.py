from django import forms

from .models import Article
from ..users.models import User

class ArticleForm(forms.ModelForm):
    author = forms.ModelMultipleChoiceField(required=True, queryset=User.objects.filter(service=False))

    class Meta:
        model = Article
        exclude = ["slug", "posted", "edited"]
