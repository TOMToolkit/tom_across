from django.shortcuts import render
from django.views.generic import TemplateView

class AcrossDashboardView(TemplateView):
    template_name = "tom_across/dashboard.html"