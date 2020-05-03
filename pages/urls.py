from django.urls import path

from pages.views import IndexView

app_name = 'members'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
]
