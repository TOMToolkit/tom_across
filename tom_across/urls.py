from django.urls import path
from tom_across.views import DemoView, ObservationTableView, visibility_plot_view

app_name = 'tom_across'
from tom_across.views import AcrossDashboardView

urlpatterns = [
    path('<int:pk>/demo', DemoView.as_view(), name='demo-page'),
    path('', DemoView.as_view(), name='demo-page'),
    path('observations/<int:target_id>/', ObservationTableView.as_view(), name='observation-table'),
    path('target/<int:pk>/visibility-plot/', visibility_plot_view, name='visibility-plot'),
    path("across/", AcrossDashboardView.as_view(), name="across")
]