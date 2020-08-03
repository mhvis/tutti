from django.urls import path

from members.views import MyPasswordChangeDoneView, MyPasswordChangeView

app_name = "members"

urlpatterns = [
    path('password_change/', MyPasswordChangeView.as_view(), name="password_change"),
    path('password_change/done/', MyPasswordChangeDoneView.as_view(), name="password_change_done"),
]
