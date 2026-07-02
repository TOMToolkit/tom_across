from django.urls import path
from tom_across import views

urlpatterns = [
    path("across/", views.AcrossDashboardView.as_view(), name="across"),
    path("observations/<int:target_id>/", views.ObservationTableView.as_view(), name="observation-table"),
]