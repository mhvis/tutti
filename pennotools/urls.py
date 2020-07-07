from django.urls import path

from pennotools.views import QRekeningView, ContributieView

app_name = 'pennotools'
urlpatterns = [
    path('qrekening/', QRekeningView.as_view(), name='qrekening'),
    path('contributie/', ContributieView.as_view(), name='contributie')
]
