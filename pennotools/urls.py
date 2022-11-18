from django.urls import path

from pennotools.views import QRekeningView, ContributionView, XmlMakerView

app_name = 'pennotools'
urlpatterns = [
    path('qrekening/', QRekeningView.as_view(), name='qrekening'),
    path('contributie/', ContributionView.as_view(), name='contribution'),
    path('xmlmaker/', XmlMakerView.as_view(), name='xmlmaker'),
]
