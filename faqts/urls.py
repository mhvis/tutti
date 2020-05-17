from django.urls import path

from faqts.views import FaQtsView

app_name = 'faqts'
urlpatterns= [
    path('', FaQtsView.as_view(), name='faqts')
]