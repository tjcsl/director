# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from django.contrib.auth.decorators import login_required
from ..authentication.decorators import superuser_required

from ...utils.emails import send_approval_request_email
from .models import SiteRequest


@login_required
def approve_view(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return redirect("request_site")

    if request.method == "POST":
        site_request = get_object_or_404(SiteRequest, id=request.POST.get("request", None))
        if site_request.teacher != request.user:
            messages.error(request, "You do not have permission to approve this request!")
            return redirect("approve_site")
        agreement = request.POST.get("agreement", False) is not False
        if not agreement:
            messages.error(request, "You must agree to the conditions in order to approve a site!")
        else:
            site_request.teacher_approval = True
            site_request.save()
            messages.success(request, "Your approval has been added and the site will be created shortly!")
        return redirect("approve_site")

    context = {
        "requests": request.user.site_requests.all().order_by("-request_date"),
        "admin_requests": SiteRequest.objects.filter(teacher_approval=True).order_by("-request_date") if request.user.is_superuser else None
    }

    return render(request, "request/approve.html", context)


@superuser_required
def approve_admin_view(request):
    if request.method == "POST":
        site_request = get_object_or_404(SiteRequest, id=request.POST.get("request", None))
        action = request.POST.get("action", None)
        if action == "accept":
            site_request.admin_approval = True
            site_request.save()
            messages.success(request, "Request has been marked as processed!")
        elif action == "reject":
            site_request.delete()
            messages.success(request, "Request deleted!")
        return redirect("admin_site")

    context = {
        "requests": SiteRequest.objects.all().order_by("-request_date") if request.user.is_superuser else None
    }

    return render(request, "request/admin.html", context)


@login_required
def request_view(request):
    if request.user.is_staff and not request.user.is_superuser:
        return redirect("approve_site")

    context = {}

    if request.method == "POST":
        activity = request.POST.get("name", None)
        extra = request.POST.get("extra", None)
        teacher = request.POST.get("teacher", None)
        agreement = request.POST.get("agreement", None)
        if not activity or not teacher:
            messages.error(request, "You must fill out all of the fields before submitting this form!")
        if not agreement:
            messages.error(request, "You must accept the agreement before submitting this form!")
        teacher = create_user(request, teacher)
        if not teacher:
            messages.error(request, "Invalid teacher selected!")
        elif not teacher.is_staff and not teacher.is_superuser:
            messages.error(request, "This user is not a teacher or staff member!")
        else:
            sr = SiteRequest.objects.create(
                user=request.user,
                teacher=teacher,
                activity=activity,
                extra_information=extra
            )
            if send_approval_request_email(sr) > 0:
                messages.success(request, "Website request created!")
            else:
                messages.warning(request, "Website request created, but failed to email teacher.")

    context["requests"] = request.user.requested_sites.filter(admin_approval=False)

    return render(request, "request/create.html", context)
