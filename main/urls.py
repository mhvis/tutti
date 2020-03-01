from django.urls import path, include

from qluis.admin import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),
    path('', include('qluis.urls')),
]
