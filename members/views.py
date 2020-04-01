from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView


class AdminRedirectView(View):
    def get(self, request, *args, **kwargs):
        return redirect('admin:index')


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'members/base.html'
