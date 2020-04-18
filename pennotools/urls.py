from django.urls import path

from pennotools.views import QrekeningView

app_name = 'pennotools'
urlpatterns = [
    path('Qrekening/', QrekeningView.as_view(), name='qrekening'),
]
