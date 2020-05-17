from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render

from django.views.generic import TemplateView


class FaQtsView(LoginRequiredMixin, TemplateView):
    template_name = "faqts/faqts.html"
