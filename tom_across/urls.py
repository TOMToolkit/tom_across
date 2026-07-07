from django.urls import path
from tom_across.views import DemoView, ObservationTableView

app_name = 'tom_across'

urlpatterns = [
    path('<int:pk>/demo', DemoView.as_view(), name='demo-page'),
    path('', DemoView.as_view(), name='demo-page'),
    path('observations/<int:target_id>/', ObservationTableView.as_view(), name='observation-table'),
]