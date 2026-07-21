from django.shortcuts import render
from django.views.generic import TemplateView
from django_tables2 import RequestConfig
from django.views.generic.list import ListView
from tom_common.htmx_table import HTMXTableViewMixin
from django_tables2 import SingleTableView
from django.urls import reverse

from across.client import Client

from tom_targets.models import Target

from tom_across.utils import observation_rows
from tom_across.tables import ObservationTable
from tom_across.forms import ObservationFilterForm
import logging

logger = logging.getLogger(__name__)

class ObservationTableView(HTMXTableViewMixin, ListView):
    table_class = ObservationTable
    template_name = "tom_across/observation_table.html"
    paginate_by = 10
    model = None

    def get_queryset(self):
        client = Client()
        target = Target.objects.get(id=self.kwargs["target_id"])
        form = ObservationFilterForm(self.request.GET or None)
        filters = {}
        if form.is_valid():
            filters = {
                'start_date': form.cleaned_data.get('start_date'),
                'end_date': form.cleaned_data.get('end_date'),
                'wavelength_min': form.cleaned_data.get('wavelength_min'),
                'wavelength_max': form.cleaned_data.get('wavelength_max'),
                'wavelength_type': form.cleaned_data.get('wavelength_type'),
                'obs_type': form.cleaned_data.get('observation_type') or None,
            }
            filters = {k: v for k, v in filters.items() if v not in (None, '')}
        return observation_rows(client, target, **filters)

    def get_context_data(self, **kwargs):
        context = super(HTMXTableViewMixin, self).get_context_data(**kwargs)
        context['record_count'] = context['paginator'].count
        context['empty_database'] = not context['object_list']
        context["target"] = Target.objects.get(id=self.kwargs["target_id"])
        context["filter_form"] = ObservationFilterForm(self.request.GET or None)
        return context
