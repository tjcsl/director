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

    class Meta:
        model = VirtualMachine
        fields = ["name", "description", "users", "site"]

    def save(self, commit=True):
        instance = forms.ModelForm.save(self, commit=False)
        hostname = slugify(instance.name).replace("_", "-")

        if commit:
            instance.save()
            self.save_m2m()
            ret = call_api("container.create", name=hostname)
            if ret is None or ret[0] == 1:
                instance.delete()
                return None
            else:
                if ret[0] != 2:
                    instance.uuid = uuid.UUID(ret[1])
                    instance.save()
                ret = call_api("container.set_config", key="lxc.cgroup.memory.limit_in_bytes", value="4G")
                if ret != 0:
                    client.captureMessage("Failed to set VM memory limit: {}".format(ret))

        return instance
