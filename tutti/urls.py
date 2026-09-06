from django.contrib import admin
from django.urls import path, include
from health_check.views import HealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('oidc/', include('oidc.urls')),
    path(
        "ht/",
        HealthCheckView.as_view(
            checks=[
                "health_check.Database",
                "health_check.Mail",
                "health_check.Storage",
            ],
        ),
        name="health_check",
    ),
    path('penno/', include('pennotools.urls')),
    path('duqduqgo/', include('duqduqgo.urls')),
    path('members/', include('members.urls')),
    path('faqts/', include('faqts.urls')),
    path('', include('pages.urls')),
]
