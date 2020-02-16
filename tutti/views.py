from django.shortcuts import redirect
from django.views import View


class AdminRedirectView(View):
    def get(self, request, *args, **kwargs):
        return redirect('admin:index')
