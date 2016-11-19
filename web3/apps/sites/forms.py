from django import forms


class CreateSiteForm(forms.Form):
    name = forms.CharField(max_length=32, widget=forms.TextInput(attrs={"class": "form-control"}))
    domain = forms.CharField(max_length=255, widget=forms.TextInput(attrs={"class": "form-control"}))
    description = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    category = forms.ChoiceField(choices=(("static", "Static"), ("php", "PHP"), ("dynamic", "Dynamic")), widget=forms.Select(attrs={"class": "form-control"}))
    purpose = forms.ChoiceField(choices=(("user", "User"), ("activity", "Activity")), widget=forms.Select(attrs={"class": "form-control"}))
