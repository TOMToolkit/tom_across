from django.urls import path
from tom_across.views import ObservationTableView, visibility_plot_view

app_name = 'tom_across'

urlpatterns = [
    path('observations/<int:target_id>/', ObservationTableView.as_view(), name='observation-table'),
    path('target/<int:pk>/visibility-plot/', visibility_plot_view, name='visibility-plot'),
]