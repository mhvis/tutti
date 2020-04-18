from django.urls import path, include

from members.admin import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),
    path('oidc/', include('oidc.urls')),
    path('ht/', include('health_check.urls')),
    path('', include('members.urls', namespace='members')),
]
