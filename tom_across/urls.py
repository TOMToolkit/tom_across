from django.urls import path
from tom_across.views import visibility_plot_view, ObservationTableView

app_name = 'tom_across'

urlpatterns = [
    path('target/<int:pk>/visibility-plot/', visibility_plot_view, name='visibility-plot'),
    path('observations/<int:target_id>/', ObservationTableView.as_view(), name='observation-table'),
]