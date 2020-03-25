from django.urls import path, include

from members.views import IndexView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('oidc/', include('mozilla_django_oidc.urls')),
]
