from django.urls import path

from members.views import IndexView

app_name = 'members'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
]
