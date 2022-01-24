from django.urls import path

from pages.views import IndexView


# This is a test view, can be removed
def server_error_view(request):
    raise RuntimeError('Test')


app_name = 'pages'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('500/', server_error_view),
]
