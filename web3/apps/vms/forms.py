import uuid

from django import forms
from django.conf import settings
from django.utils.text import slugify

from ..users.models import User
from .models import VirtualMachine
from .helpers import call_api


class VirtualMachineForm(forms.ModelForm):
    name = forms.CharField(max_length=32, widget=forms.TextInput(attrs={"class": "form-control"}))
    description = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}), required=False)
    users = forms.ModelMultipleChoiceField(required=False, queryset=User.objects.filter(service=False))

    class Meta:
        model = VirtualMachine
        fields = ["name", "description", "users"]


    def save(self, commit=True):
        instance = forms.ModelForm.save(self, commit=False)

        if commit:
            instance.save()
            self.save_m2m()
            ret = call_api("container.create", name=str(instance.uuid))
            if ret[0] == 1:
                instance.delete()
                return None
            else:
                if ret[0] != 2:
                    instance.uuid = uuid.UUID(ret[1])
                    instance.save()
                call_api("container.set_hostname", name=str(instance.uuid), new_hostname=slugify(instance.name).replace("_", "-"))

        return instance
