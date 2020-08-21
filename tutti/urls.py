from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('oidc/', include('oidc.urls')),
    path('ht/', include('health_check.urls')),
    path('penno/', include('pennotools.urls')),
    path('duqduqgo/', include('duqduqgo.urls')),
    path('members/', include('members.urls')),
    path('faqts/', include('faqts.urls')),
    path('', include('pages.urls')),
]
