from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def send_new_site_email(user, site):
    context = {"user": user, "site": site}
    plain_message = render_to_string("emails/new_site_added.txt", context)
    html_message = render_to_string("emails/new_site_added.html", context)
    if settings.DEBUG:
        print(plain_message)
        return 0
    else:
        return send_mail("{} You've been added to a new website!".format(settings.EMAIL_SUBJECT_PREFIX),
                         plain_message, settings.EMAIL_FROM,
                         [user.email], html_message=html_message)


def send_approval_request_email(request):
    context = {"request": request}
    plain_message = render_to_string("emails/approval_request.txt", context)
    html_message = render_to_string("emails/approval_request.html", context)
    if settings.DEBUG:
        print(plain_message)
        return 0
    else:
        return send_mail("{} A website request needs your approval!".format(settings.EMAIL_SUBJECT_PREFIX),
                         plain_message, settings.EMAIL_FROM,
                         [request.teacher.email], html_message=html_message)


def send_feedback_email(request, comments):
    context = {"request": request, "feedback": comments}
    plain_message = render_to_string("emails/feedback.txt", context)
    html_message = render_to_string("emails/feedback.html", context)
    if settings.DEBUG:
        print(plain_message)
        return 0
    else:
        return send_mail("{} Director Feedback".format(settings.EMAIL_SUBJECT_PREFIX),
                        plain_message, settings.EMAIL_FROM,
                        [settings.EMAIL_FEEDBACK], html_message=html_message)
