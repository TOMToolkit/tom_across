from django.urls import path
from tom_across.views import ObservationTableView

app_name = 'tom_across'

urlpatterns = [
    path('observations/<int:target_id>/', ObservationTableView.as_view(), name='observation-table'),
]