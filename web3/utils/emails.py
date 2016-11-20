from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def send_new_site_email(user, site):
    if site.category == "user":
        url = "https://user.tjhsst.edu/{}/".format(site.name)
    elif site.category == "activity":
        url = "https://activities.tjhsst.edu/{}/".format(site.name)
    elif site.category == "legacy":
        url = "https://tjhsst.edu/~{}/".format(site.name)
    else:
        url = site.domain.split()[0]
    context = {"user": user, "site": site, "url": url}
    plain_message = render_to_string("emails/new_site_added.txt", context)
    html_message = render_to_string("emails/new_site_added.html", context)
    if settings.DEBUG:
        print(plain_message)
        return 0
    else:
        return send_mail("{} You've been added to a new website!".format(settings.EMAIL_SUBJECT_PREFIX),
                         plain_message, settings.EMAIL_FROM,
                         [user.email], html_message=html_message)
