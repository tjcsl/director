import pwd
import subprocess
import traceback
import xml.etree.ElementTree as ElementTree

import os
import re
import shutil
from django import forms
from django.conf import settings
from raven.contrib.django.raven_compat.models import client

from .models import VirtualMachine, VirtualMachineHost
from ..sites.models import Site
from ..users.models import User


def gen_random_mac():
    mac = b'\x02\x00\x00' + os.urandom(3)
    # Setting this bit marks the mac address as locally administered
    # make hex
    mac = mac.hex()
    # add colons
    mac = ':'.join(mac[i * 2:i * 2 + 2] for i in range(6))
    return mac


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
                    template = VirtualMachine.objects.get(name=self.cleaned_data['template'])
                    subprocess.run(
                        ['rsync', '-ar', os.path.dirname(template.root_path) + '/',
                         os.path.dirname(instance.root_path) + '/'],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    # Coerce the XML into being right and define the domain
                    mac = gen_random_mac()
                    dom_xml = ElementTree.fromstring(template.domain.XMLDesc())
                    dom_xml.find('name').text = instance.internal_name
                    dom_xml.find('uuid').text = str(instance.uuid)
                    dom_xml.find('devices').find('interface').find('mac').attrib['address'] = mac
                    dom_xml.find('devices').find('filesystem').find('source').attrib['dir'] = instance.root_path
                    instance.host.connection.defineXML(ElementTree.tostring(dom_xml).decode('utf8'))
                    # Add host to DHCP
                    host_sub = ElementTree.Element("host")
                    host_sub.set('mac', mac)
                    host_sub.set('name', instance.internal_name)
                    host_sub.set('ip', '192.168.122.6')
                    # excuse me what the f why doesn't this update running config
                    subprocess.run(
                        ['virsh', '-c', 'lxc+ssh://root@' + instance.host.hostname + '/', 'net-update',
                         settings.LIBVIRT_NET, 'add', 'ip-dhcp-host', ElementTree.tostring(host_sub).decode('utf8')])
                    # Generate and set perms on SSH key
                    privkey_path = '/home/' + instance.owner.username + '/.ssh/' + str(instance.uuid)
                    subprocess.run(['ssh-keygen', '-N', '', '-f', privkey_path])
                    unix_user = pwd.getpwnam(instance.owner.username)
                    os.chown(privkey_path, unix_user.pw_uid, unix_user.pw_gid)
                    os.chmod(privkey_path, 0o600)
                    os.chown(privkey_path + '.pub', unix_user.pw_uid, unix_user.pw_gid)
                    os.chmod(privkey_path + '.pub', 0o600)
                    # Copy SSH key to domain
                    # TODO figure out if we need to change perms on the instance files
                    authkeys_path = os.path.join(instance.root_path, 'root', '.ssh', 'authorized_keys')
                    instance_ssh_path = os.path.dirname(authkeys_path)
                    if not os.path.exists(instance_ssh_path):
                        os.mkdir(instance_ssh_path)
                    shutil.copy(privkey_path + '.pub', authkeys_path)
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
                    client.captureMessage("Failed to change VM hostname: Not implemented")

        return instance

    class Meta:
        model = VirtualMachine
        fields = ["name", "description", "owner", "users", "site", "host", "is_template"]


def get_named_elements(xml_tree, element_name):
    return [e for e in xml_tree if e.tag == element_name]
