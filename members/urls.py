from django.urls import path

from members.views import IndexView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
]
