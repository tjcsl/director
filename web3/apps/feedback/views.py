# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect
from django.contrib import messages

from ...utils.emails import send_feedback_email

def feedback_view(request):
    if request.method == "POST":
        comments = request.POST.get("feedback", None)
        send_feedback_email(request, comments)
        messages.success(request, "Your feedback has been received! Thanks!")
        return redirect("index")
    return render(request, "feedback/feedback.html")
