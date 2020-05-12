from django.urls import path

from duqduqgo.views import Qalendar, Birthdays

app_name = 'duqduqgo'
urlpatterns = [
    path('qalendar/', Qalendar.as_view(), name='qalendar'),
    path('birthday_events/', Birthdays.as_view()),
]
