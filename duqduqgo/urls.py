from django.urls import path

from duqduqgo.views import Qalendar

app_name = 'pennotools'
urlpatterns = [
    path('qalendar/', Qalendar.as_view(), name='qalendar'),
]
