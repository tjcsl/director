import uuid

from django import forms
from django.conf import settings
from django.utils.text import slugify

from ..users.models import User
from ..sites.models import Site
from .models import VirtualMachine
from .helpers import call_api

from raven.contrib.django.raven_compat.models import client


class VirtualMachineForm(forms.ModelForm):
    name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={"class": "form-control"}))
    description = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}), required=False)
    users = forms.ModelMultipleChoiceField(required=False, queryset=User.objects.filter(service=False))
    site = forms.ModelChoiceField(required=False, queryset=Site.objects.filter(category="vm"), widget=forms.Select(attrs={"class": "form-control"}))

    def __init__(self, *args, **kwargs):
        super(VirtualMachineForm, self).__init__(*args, **kwargs)
        if not(self.instance and self.instance.pk):
            self.fields["template"] = forms.ChoiceField(choices=[(x, x.title()) for x in call_api("container.templates")],
                                                        widget=forms.Select(attrs={"class": "form-control"}))

    def save(self, commit=True):
        instance = forms.ModelForm.save(self, commit=False)
        hostname = slugify(instance.name).replace("_", "-")

        if commit:
            instance.save()
            self.save_m2m()
            ret = call_api("container.create", name=hostname, template=self.cleaned_data.get("template", "debian"))
            if ret is None or ret[0] == 1:
                client.captureMessage("Failed to create VM: {}".format(ret))
                instance.delete()
                return None
            else:
                if ret[0] != 2:
                    instance.uuid = uuid.UUID(ret[1])
                    instance.save()

        return instance

    class Meta:
        model = VirtualMachine
        fields = ["name", "description", "users", "site"]
