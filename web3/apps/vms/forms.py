from django import forms
from django.conf import settings

from ..users.models import User
from .models import VirtualMachine


class VirtualMachineForm(forms.ModelForm):
    name = forms.CharField(max_length=32, widget=forms.TextInput(attrs={"class": "form-control"}))
    description = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}), required=False)
    users = forms.ModelMultipleChoiceField(required=False, queryset=User.objects.filter(service=False))

    class Meta:
        model = VirtualMachine
        fields = ["name", "description", "users"]
