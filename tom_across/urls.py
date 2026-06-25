from django.urls import path
from tom_across.views import AcrossDashboardView

urlpatterns = [
    path("across/", AcrossDashboardView.as_view(), name="across")
]