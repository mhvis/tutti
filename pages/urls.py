from django.urls import path

from pages.views import IndexView

app_name = 'pages'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
]
