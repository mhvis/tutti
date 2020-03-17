from django.urls import path, include

from members.admin import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),
    path('', include('members.urls')),
]
