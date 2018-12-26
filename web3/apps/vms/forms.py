import uuid

import os
import re
import shutil
from django import forms
from django.conf import settings
from raven.contrib.django.raven_compat.models import client

from .models import VirtualMachine, VirtualMachineHost
from ..sites.models import Site
from ..users.models import User


class VirtualMachineForm(forms.ModelForm):
    name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={"class": "form-control"}))
    description = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}), required=False)
    users = forms.ModelMultipleChoiceField(required=False, queryset=User.objects.filter(service=False))
    site = forms.ModelChoiceField(required=False, queryset=Site.objects.filter(category="vm"))
    owner = forms.ModelChoiceField(required=True, queryset=User.objects.filter(service=False))
    host = forms.ModelChoiceField(required=True, queryset=VirtualMachineHost.objects.all(), widget=forms.RadioSelect(),
                                  empty_label=None)
    is_template = forms.BooleanField(required=False)

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        name_re = "^{}$".format(re.escape(name.lower().replace("-", " ")).replace("\\\\-", "[- ]"))
        existing = VirtualMachine.objects.filter(name__iregex=name_re)
        if existing.exists():
            if self.instance and self.instance.pk:
                if not existing.first() == self.instance:
                    raise forms.ValidationError("A virtual machine with this name already exists!")
            else:
                raise forms.ValidationError("A virtual machine with this name already exists!")
        return name

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(VirtualMachineForm, self).__init__(*args, **kwargs)
        self.fields["host"].initial = VirtualMachineHost.objects.first().id
        self.fields["owner"].initial = self.user.id
        if not self.user.is_superuser:
            self.fields["owner"].queryset = User.objects.filter(id=self.user.id)
            self.fields["owner"].disabled = True
            self.fields["site"].queryset = Site.objects.filter(group__users=self.user, category="vm")
            self.fields["is_template"].disabled = True
        if self.instance and self.instance.pk:
            self.old_hostname = self.instance.hostname
        else:
            templates = VirtualMachine.objects.all().filter(is_template=True)
            self.fields["template"] = forms.ChoiceField(choices=[(x, x.name) for x in templates],
                                                        widget=forms.Select(attrs={"class": "form-control"}),
                                                        required=True)

    def save(self, commit=True):
        instance = forms.ModelForm.save(self, commit=False)
        hostname = instance.hostname

        if commit:
            editing = bool(instance.pk)
            instance.save()
            self.save_m2m()
            instance.users.remove(instance.owner)
            if not editing:
                # TODO: Create VM _asynchronously_
                client.captureMessage("Creating VM...")
                template_path = os.path.join(settings.LXC_PATH, self.template.hostname + "-" + str(self.template.uuid))
                new_path = os.path.join(settings.LXC_PATH, instance.hostname + "-" + str(instance.uuid))
                shutil.copytree(template_path, new_path)
                # i'm lazy and this is bad
                old_xml = self.template.get_domain().
                if ret is None or ret[0] == 1:
                    client.captureMessage("Failed to create VM: {}".format(ret))
                    instance.delete()
                    return None
                else:
                    if ret[0] != 2:
                        instance.uuid = uuid.UUID(ret[1].split("\n")[-1])
                        instance.save()
            elif not self.old_hostname == hostname:
                if "name" in self.changed_data:
                    # TODO change hostname
                    if ret is None or ret != 0:
                        client.captureMessage("Failed to change VM hostname: {}".format(ret))
                        return instance

        return instance

    class Meta:
        model = VirtualMachine
        fields = ["name", "description", "owner", "users", "site", "host", "is_template"]
