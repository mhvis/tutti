import os.path
from datetime import date

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/home.html'


class AboutView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/about.html'

    def get_context_data(self, **kwargs):
        """Loads app build date from file."""
        context = super().get_context_data(**kwargs)
        build_date = None
        try:
            with open(os.path.join(settings.BASE_DIR, "builddate.txt")) as f:
                build_date = date.fromisoformat(f.read().strip())
        except FileNotFoundError:
            pass
        context['build_date'] = build_date
        return context
