from django.urls import path

from duqduqgo.views import Qalendar, Birthdays

app_name = 'duqduqgo'
urlpatterns = [
    path('calendar/', Qalendar.as_view(), name='qalendar'),
    path('birthdays/', Birthdays.as_view(), name="birthdays"),
]
