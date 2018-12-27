import subprocess
import sys
import traceback

import os
import re
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
    is_template = forms.BooleanField(required=False,
                                     widget=forms.CheckboxInput(attrs={"class": "custom-control-input"}))

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
                # Create the VM instead of editing it
                try:
                    # TODO: Create VM _asynchronously_
                    # ok it legit needs to be async
                    print("hello", file=sys.stderr)
                    template = VirtualMachine.objects.get(name=self.cleaned_data['template'])
                    old_congealed = template.hostname + "-" + str(template.uuid)
                    new_congealed = hostname + "-" + str(instance.uuid)
                    template_path = os.path.join(settings.LXC_PATH, old_congealed)
                    new_path = os.path.join(settings.LXC_PATH, new_congealed)
                    print("hello2", file=sys.stderr)
                    # shutil.copytree(template_path, new_path)
                    subprocess.run(['rsync', '-ar', os.path.join(template_path, 'rootfs'), new_path],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    # i'm lazy and this is bad
                    old_xml = template.get_domain().XMLDesc()
                    new_xml = old_xml.replace(old_congealed, new_congealed).replace(str(template.uuid),
                                                                                    str(instance.uuid))
                    print("hello3", file=sys.stderr)
                    instance.host.connection.defineXML(new_xml)
                    instance.save()
                except Exception as e:
                    client.captureMessage("Failed to create VM: {}".format(e))
                    with open("/exc", 'w') as f:  # le hacc
                        traceback.print_exc(file=f)
                    instance.delete()
                    return None
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
