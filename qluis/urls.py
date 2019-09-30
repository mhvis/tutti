from django.urls import path

from qluis.views import AdminRedirectView

urlpatterns = [
    path('', AdminRedirectView.as_view(), name='index'),
]
