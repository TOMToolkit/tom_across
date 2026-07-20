import json
from datetime import datetime, timedelta, timezone
from itertools import combinations

from django.core.cache import cache
from django.conf import settings
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.list import ListView
from plotly import graph_objs as go
from plotly import offline
from plotly.subplots import make_subplots

from across.client import Client
from tom_common.htmx_table import HTMXTableViewMixin
from tom_targets.models import Target
from tom_across.forms import ObservationFilterForm, VisibilityPlotForm
from tom_across.tables import ObservationTable
from tom_across.utils import observation_rows, get_observatory_name_id_map, visibility_from_instrument
import logging

logger = logging.getLogger(__name__)

class DemoView(TemplateView):
    """
    Generic demo view
    """
    template_name = "tom_across/demo_page.html"

class ObservationTableView(HTMXTableViewMixin, ListView):
    table_class = ObservationTable
    template_name = "tom_across/observation_table.html"
    paginate_by = 10
    model = None

    def get_queryset(self):
        client = Client()
        target = Target.objects.get(id=self.kwargs["pk"])
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
        context["target"] = Target.objects.get(id=self.kwargs["pk"])
        context["filter_form"] = ObservationFilterForm(self.request.GET or None)
        return context

def visibility_plot_view(request, pk):
    target = Target.objects.get(id=pk)
    if target.type != 'SIDEREAL':
        return render(request, 'tom_across/partials/visibility_plot.html', {'plot': None})
    
    client = Client()
    names = sorted(set(get_observatory_name_id_map(client).values()))
    observatory_choices = [(n, n) for n in names]
    now = datetime.now()
    default_observatories = settings.ACROSS_VIS_OBSERVATORIES if settings.ACROSS_VIS_OBSERVATORIES else ['HST', 'JWST', 'Swift']
    defaults = {'observatories': default_observatories, 'begin': now, 'end': now + timedelta(hours=24)}
    form = VisibilityPlotForm(request.GET or defaults, observatory_choices=observatory_choices)
    if form.is_valid():
        observatory_list = form.cleaned_data['observatories']
        date_range_begin = form.cleaned_data['begin']
        date_range_end = form.cleaned_data['end']
        if date_range_begin.tzinfo is not None:
            date_range_begin = date_range_begin.astimezone(timezone.utc).replace(tzinfo=None)
        if date_range_end.tzinfo is not None:
            date_range_end = date_range_end.astimezone(timezone.utc).replace(tzinfo=None)
    else:
        observatory_list, date_range_begin, date_range_end = defaults['observatories'], defaults['begin'], defaults['end']

    context = visibility_from_instrument(target, client, observatory_list, date_range_begin = date_range_begin, date_range_end = date_range_end)
    context['form'] = form
    return render(request, 'tom_across/partials/visibility_plot.html', context)

class AcrossDashboardView(TemplateView):
    template_name = "tom_across/dashboard.html"