from django.urls import path

from members.views import PasswordChangeView, PasswordChangeDoneView

app_name = "members"

urlpatterns = [
    path('password_change/', PasswordChangeView.as_view(), name="password_change"),
    path('password_change/done/', PasswordChangeDoneView.as_view(), name="password_change_done"),
]
