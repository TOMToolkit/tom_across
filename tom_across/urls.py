from django.urls import path
from tom_across import views

urlpatterns = [
    path("across/", views.AcrossDashboardView.as_view(), name="across"),
    path("targets/<int:target_id>/observations/",views.observation_table_view, name="observation-table")
]