from django.core.mail import EmailMultiAlternatives, send_mail
from django.conf import settings
from django.template.loader import render_to_string


def send_new_site_email(user, site):
    """Send email informing user about being added to a new site."""
    context = {"user": user, "site": site, "contact_email": settings.EMAIL_CONTACT}
    plain_message = render_to_string("emails/new_site_added.txt", context)
    html_message = render_to_string("emails/new_site_added.html", context)
    if settings.DEBUG:
        print(plain_message)
        return 0
    else:
        return send_mail(
            "{} You've been added to a new website!".format(
                settings.EMAIL_SUBJECT_PREFIX
            ),
            plain_message,
            settings.EMAIL_FROM,
            [user.email],
            html_message=html_message,
        )


def send_approval_request_email(request):
    """Send email to teachers after students have submitted a site request."""
    context = {"request": request, "contact_email": settings.EMAIL_CONTACT}
    plain_message = render_to_string("emails/approval_request.txt", context)
    html_message = render_to_string("emails/approval_request.html", context)
    if settings.DEBUG:
        print(plain_message)
        return 0
    else:
        msg = EmailMultiAlternatives(
            subject="{} A website request ({}) needs your approval!".format(
                settings.EMAIL_SUBJECT_PREFIX, request.activity
            ),
            body=plain_message,
            from_email=settings.EMAIL_FROM,
            to=[request.teacher.email],
            reply_to=[settings.EMAIL_FEEDBACK],
        )
        msg.attach_alternative(html_message, "text/html")
        return msg.send()


def send_admin_request_email(request):
    """Send email to administrators after teachers have approved a site request."""
    context = {"request": request}
    plain_message = render_to_string("emails/admin_request.txt", context)
    html_message = render_to_string("emails/admin_request.html", context)
    if settings.DEBUG:
        print(plain_message)
        return 0
    else:
        subject = "{} A website request ({} - {}) requires processing!"
        msg = EmailMultiAlternatives(
            subject=subject.format(
                settings.EMAIL_SUBJECT_PREFIX, request.activity, request.user.full_name
            ),
            body=plain_message,
            from_email=settings.EMAIL_FROM,
            to=[settings.EMAIL_FEEDBACK],
            reply_to=[request.user.email, settings.EMAIL_FEEDBACK],
        )
        msg.attach_alternative(html_message, "text/html")
        return msg.send()


def send_feedback_email(request, comments):
    context = {
        "request": request,
        "feedback": comments,
        "useragent": request.META["HTTP_USER_AGENT"],
        "remote_ip": get_remote_ip(request),
    }
    plain_message = render_to_string("emails/feedback.txt", context)
    html_message = render_to_string("emails/feedback.html", context)
    if settings.DEBUG:
        print(plain_message)
        return 0
    else:
        msg = EmailMultiAlternatives(
            subject="{} Feedback from {}".format(
                settings.EMAIL_SUBJECT_PREFIX, request.user.username
            ),
            body=plain_message,
            from_email=settings.EMAIL_FROM,
            to=[settings.EMAIL_FEEDBACK],
            reply_to=[request.user.email, settings.EMAIL_FEEDBACK],
        )
        msg.attach_alternative(html_message, "text/html")
        return msg.send()


def get_remote_ip(request):
    if "HTTP_X_FORWARDED_FOR" in request.META:
        ip = request.META.get("HTTP_X_FORWARDED_FOR")
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip
