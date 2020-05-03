from django.urls import path

from pennotools.views import QRekeningView

app_name = 'pennotools'
urlpatterns = [
    path('qrekening/', QRekeningView.as_view(), name='qrekening'),
]
