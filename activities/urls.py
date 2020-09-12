from django.urls import path
from activities.views import ActivitiesView, ActivityView, MyActivityFormView, PastActivitiesView

app_name = "activities"

urlpatterns = [
    path('', ActivitiesView.as_view(), name="index"),
    path('past/', PastActivitiesView.as_view(), name="past"),
    path('activity/<int:id>/', ActivityView.as_view(), name="activity"),
    path('activity/<int:id>/edit/', MyActivityFormView.as_view(), name="myactivity"),
]
