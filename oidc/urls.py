from django.urls import path

from oidc import views

app_name = 'oidc'
urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('auth/', views.AuthView.as_view(), name='auth'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('loggedout/', views.LoggedOutView.as_view(), name='loggedout'),
]
