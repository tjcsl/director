from django import template
register = template.Library()


@register.filter("field_type")
def field_type(obj):
    return obj.field.widget.__class__.__name__


@register.filter("startswith")
def startswith(obj, txt):
    if isinstance(obj, str):
        return obj.startswith(txt)
    return False
