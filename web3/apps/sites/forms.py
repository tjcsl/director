from django import forms


class CreateSiteForm(forms.Form):
    name = forms.CharField(max_length=32, widget=forms.TextInput(attrs={"class": "form-control"}))
    domain = forms.CharField(max_length=255, widget=forms.TextInput(attrs={"class": "form-control"}), help_text="Can only contain A-Z, a-z, 0-9 and the - character. Separate multiple domains through spaces.")
    description = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    category = forms.ChoiceField(choices=(("static", "Static"), ("php", "PHP"), ("dynamic", "Dynamic")), widget=forms.Select(attrs={"class": "form-control"}))
    purpose = forms.ChoiceField(choices=(("user", "User"), ("activity", "Activity")), widget=forms.Select(attrs={"class": "form-control"}))
