# -*- coding: utf-8 -*-
from django.shortcuts import render


def feedback_view(request):
    return render(request, "feedback/feedback.html")
