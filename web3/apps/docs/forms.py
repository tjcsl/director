from django import forms

from .models import Article
from ..users.models import User


class ArticleForm(forms.ModelForm):
    author = forms.ModelMultipleChoiceField(required=True, queryset=User.objects.filter(service=False))
    reason = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Change Reason'}))
    tags = forms.CharField(required=False)

    class Meta:
        fields = ['title', 'author', 'content']
        model = Article
