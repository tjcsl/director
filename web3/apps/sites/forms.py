from django import forms
from django.core.validators import RegexValidator
from django.conf import settings

from .models import Site
from .helpers import create_site_users, make_site_dirs, create_config_files

from ..users.models import User, Group


class SiteForm(forms.ModelForm):
    domain_validator = RegexValidator(r"^[0-9a-zA-Z_\- .]*$", "Only alphanumeric characters, underscores, dashes, and spaces are allowed.")

    name = forms.CharField(max_length=32, widget=forms.TextInput(attrs={"class": "form-control"}))
    domain = forms.CharField(max_length=255, widget=forms.TextInput(
        attrs={"class": "form-control"}),
        help_text="Can only contain A-Z, a-z, 0-9, dashes, and underscores. Separate multiple domains through spaces.", validators=[domain_validator])
    description = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}), required=False)
    category = forms.ChoiceField(choices=(("static", "Static"), ("php", "PHP"), ("dynamic", "Dynamic")),
                                 widget=forms.Select(attrs={"class": "form-control"}))
    purpose = forms.ChoiceField(choices=(("user", "User"), ("activity", "Activity"), ("other", "Other")), widget=forms.Select(attrs={"class": "form-control"}))
    users = forms.ModelMultipleChoiceField(queryset=User.objects.filter(service=False), widget=forms.SelectMultiple(attrs={"class": "form-control"}))

    def __init__(self, *args, **kwargs):
        if kwargs.get("instance"):
            initial = kwargs.setdefault('initial', {})
            initial["users"] = [u.pk for u in kwargs['instance'].group.users.all()]
        forms.ModelForm.__init__(self, *args, **kwargs)

    def save(self, commit=True):
        instance = forms.ModelForm.save(self, commit=False)
        print(instance)

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
            instance.save()
            self.save_m2m()
        return instance

    class Meta:
        model = Site
        fields = ["name", "domain", "description", "category", "purpose", "users"]
