from django.urls import path

from faqts.views import FaQtsView, GroupsView

app_name = 'faqts'
urlpatterns = [
    path('graphs/', FaQtsView.as_view(), name='faqts'),
    path('members/', GroupsView.as_view(), name='groups'),
]
