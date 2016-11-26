import os

from django import forms
from django.core.validators import RegexValidator
from django.conf import settings

from .models import Site, Process, Database
from .helpers import create_site_users, make_site_dirs, create_config_files, flush_permissions, create_postgres_database, create_mysql_database. delete_site_process, reload_services

from ..users.models import User, Group


class SiteForm(forms.ModelForm):
    name_validator = RegexValidator(r"^[0-9a-zA-Z_\-]*$", "Only alphanumeric characters, underscores, and dashes are allowed.")
    domain_validator = RegexValidator(r"^[0-9a-zA-Z_\- .]*$", "Only alphanumeric characters, underscores, dashes, and spaces are allowed.")

    name = forms.CharField(max_length=32,
                           widget=forms.TextInput(attrs={"class": "form-control"}),
                           help_text="Can only contain alphanumeric characters, underscores, and dashes.",
                           validators=[name_validator])
    domain = forms.CharField(max_length=255,
                             widget=forms.TextInput(attrs={"class": "form-control"}),
                             help_text="Can only contain alphanumeric characters, underscores, and dashes. Separate multiple domains through spaces.",
                             validators=[domain_validator])
    description = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}), required=False)
    category = forms.ChoiceField(choices=(("static", "Static"), ("php", "PHP"), ("dynamic", "Dynamic")),
                                 widget=forms.Select(attrs={"class": "form-control"}))
    purpose = forms.ChoiceField(choices=(("user", "User"), ("activity", "Activity"), ("other", "Other")),
                                widget=forms.Select(attrs={"class": "form-control"}))
    users = forms.ModelMultipleChoiceField(required=False, queryset=User.objects.filter(service=False))
    custom_nginx = forms.BooleanField(required=False,
                                      label="Custom Nginx Configuration",
                                      widget=forms.CheckboxInput(attrs={"class": "custom-control-input"}))

    def __init__(self, *args, **kwargs):
        if kwargs.get("instance"):
            initial = kwargs.setdefault('initial', {})
            initial["users"] = [u.pk for u in kwargs['instance'].group.users.filter(service=False)]
        if kwargs.get("user"):
            self._user = kwargs["user"]
            del kwargs["user"]
        forms.ModelForm.__init__(self, *args, **kwargs)
        instance = getattr(self, "instance", None)
        if instance and instance.pk:
            self.fields["name"].disabled = True
            if hasattr(self, "_user") and not self._user.is_superuser and not self._user.is_staff:
                for field in self.fields:
                    self.fields[field].disabled = True
                self.fields["category"].disabled = False

    def save(self, commit=True):
        instance = forms.ModelForm.save(self, commit=False)

        old_save_m2m = self.save_m2m

        def save_m2m():
            old_save_m2m()
            instance.group.users.clear()
            instance.group.users.add(instance.user)
            for user in self.cleaned_data['users']:
                instance.group.users.add(user)
        self.save_m2m = save_m2m
        if commit:
            try:
                u = instance.user
                g = instance.group
            except (User.DoesNotExist, Group.DoesNotExist):
                create_site_users(instance)
            if not settings.DEBUG:
                make_site_dirs(instance)
                create_config_files(instance)
                flush_permissions()

            if site.category != "dynamic" and site.process:
                if not settings.DEBUG:
                    delete_site_process(site.process)
                    reload_services()
                site.process.delete()

            instance.save()
            self.save_m2m()
        return instance

    class Meta:
        model = Site
        fields = ["name", "domain", "description", "category", "purpose", "users", "custom_nginx"]


class ProcessForm(forms.ModelForm):

    def __init__(self, user, *args, **kwargs):
        super(ProcessForm, self).__init__(*args, **kwargs)
        if not user.is_superuser:
            self.fields['site'].queryset = Site.objects.filter(group__users__id=user.id).filter(category="dynamic")

    path_validator = RegexValidator(r"^/web/.*$", "Please enter a valid path starting with /web.")

    site = forms.ModelChoiceField(queryset=Site.objects.filter(category="dynamic"), disabled=True)

    path = forms.CharField(max_length=255,
                           widget=forms.TextInput(attrs={"class": "form-control"}),
                           help_text="Enter a valid path starting with /web.",
                           validators=[path_validator])

    def clean_path(self):
        value = os.path.abspath(self.cleaned_data["path"].strip())
        if self.instance.pk:
            root_path = self.instance.site.path
        else:
            root_path = Site.objects.get(id=self.initial["site"]).path

        if not settings.DEBUG and not os.path.isfile(value):
            raise forms.ValidationError("The script you are trying to reference does not exist!")

        if not value.startswith(root_path):
            raise forms.ValidationError("The script you are trying to reference must be in the {} folder!".format(root_path))

        return value

    class Meta:
        model = Process
        fields = ["site", "path"]


class DatabaseForm(forms.ModelForm):
    site = forms.ModelChoiceField(queryset=Site.objects.all(), disabled=True)
    category = forms.ChoiceField(choices=(("postgresql", "PostgreSQL"), ("mysql", "MySQL")),
                                 widget=forms.RadioSelect(), label="Type")


    def __init__(self, user, *args, **kwargs):
        super(DatabaseForm, self).__init__(*args, **kwargs)
        self.initial["category"] = "postgresql"
        if not user.is_superuser:
            self.fields['site'].queryset = Site.objects.exclude(category="static").filter(group__users__id=user.id)


    def save(self, commit=True):
        instance = forms.ModelForm.save(self, commit=False)

        instance.password = User.objects.make_random_password(length=24)

        if commit:
            instance.save()
            if not settings.DEBUG:
                flag = False
                if instance.category == "postgresql":
                    flag = create_postgres_database(instance)
                elif instance.category == "mysql":
                    flag = create_mysql_database(instance)
                if not flag:
                    instance.delete()
                    return None

        return instance

    class Meta:
        model = Database
        fields = ["site", "category"]
