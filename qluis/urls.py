from django.urls import path

from qluis.views import IndexView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
]
