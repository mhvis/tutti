from django.urls import path

from tutti.views import AdminRedirectView

urlpatterns = [
    path('', AdminRedirectView.as_view(), name='index'),
]
