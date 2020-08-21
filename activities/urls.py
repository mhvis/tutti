from django.urls import path
from activities.views import ActivityView


app_name = "activities"

urlpatterns = [
    path('', ActivityView.as_view(), name="activities"),
]
