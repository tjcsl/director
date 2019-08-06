# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from ...utils.emails import send_feedback_email
from .models import Feedback


@login_required
def feedback_view(request):
    if request.method == "POST":
        comments = request.POST.get("feedback", None)
        Feedback.objects.create(user=request.user, comments=comments)
        send_feedback_email(request, comments)
        messages.success(request, "Your feedback has been received! Thanks!")
        return redirect("index")
    return render(request, "feedback/feedback.html")
