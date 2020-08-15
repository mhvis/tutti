from django.contrib.auth.views import PasswordChangeDoneView, PasswordChangeView
from django.urls import reverse_lazy

from members.forms import MyPasswordChangeForm


class MyPasswordChangeView(PasswordChangeView):
    template_name = "members/password_change_form.html"
    success_url = reverse_lazy("members:password_change_done")
    form_class = MyPasswordChangeForm


class MyPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = "members/password_change_done.html"
