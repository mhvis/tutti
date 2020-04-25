from django.conf import settings


def version_info(request):
    """See VERSION_* settings."""
    return {
        'VERSION_DATE': settings.VERSION_DATE,
        'VERSION_URL': settings.VERSION_URL,
    }
