from django import forms
from django.core.validators import RegexValidator

class CreateSiteForm(forms.Form):
    domain_validator = RegexValidator(r"^[0-9a-zA-Z_\- ]*$", "Only alphanumeric characters, underscores, dashes, and spaces are allowed.")

    name = forms.CharField(max_length=32, widget=forms.TextInput(attrs={"class": "form-control"}))
    domain = forms.CharField(max_length=255, widget=forms.TextInput(attrs={"class": "form-control"}), help_text="Can only contain A-Z, a-z, 0-9, dashes, and underscores. Separate multiple domains through spaces.", validators=[domain_validator])
    description = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    category = forms.ChoiceField(choices=(("static", "Static"), ("php", "PHP"), ("dynamic", "Dynamic")), widget=forms.Select(attrs={"class": "form-control"}))
    purpose = forms.ChoiceField(choices=(("user", "User"), ("activity", "Activity")), widget=forms.Select(attrs={"class": "form-control"}))
