from django.urls import path
from tom_across.views import visibility_plot_view

app_name = 'tom_across'

urlpatterns = [
    path('target/<int:pk>/visibility-plot/', visibility_plot_view, name='visibility-plot'),
]