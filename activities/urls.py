from django.urls import path
from activities.views import ActivitiesView, ActivityView


app_name = "activities"

urlpatterns = [
    path('', ActivitiesView.as_view(), name="index"),
    path('activity/<int:id>/', ActivityView.as_view(), name="activity"),
]
