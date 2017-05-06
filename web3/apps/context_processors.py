from django.conf import settings


def email(request):
    return {
        "contact_email": settings.EMAIL_CONTACT
    }
