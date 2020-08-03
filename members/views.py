from django.contrib.auth.views import PasswordChangeView as DjangoPasswordChangeView, \
    PasswordChangeDoneView as DjangoPasswordChangeDoneView
from django.urls import reverse_lazy


class PasswordChangeView(DjangoPasswordChangeView):
    template_name = "members/password_change_form.html"
    success_url = reverse_lazy("members:password_change_done")


class PasswordChangeDoneView(DjangoPasswordChangeDoneView):
    template_name = "members/password_change_done.html"
