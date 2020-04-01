from django.contrib.auth.views import LogoutView
from django.urls import path

from oidc import views

app_name = 'oidc'
urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('auth/', views.AuthView.as_view(), name='auth'),
    path('logout/', LogoutView.as_view(), name='logout'),  # We use the built-in logout view
]
