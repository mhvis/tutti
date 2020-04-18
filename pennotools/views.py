from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class QrekeningView(LoginRequiredMixin, TemplateView):
    template_name = 'pennotools/qrekening.html'
