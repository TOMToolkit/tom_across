import json
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.shortcuts import render
from django.views.generic.list import ListView

from tom_targets.models import Target
from tom_common.htmx_table import HTMXTableViewMixin
from tom_across.forms import VisibilityPlotForm, ObservationFilterForm
from tom_across.utils import get_observatory_name_id_map, visibility_from_instrument, observation_rows
from tom_across.tables import ObservationTable
import logging

logger = logging.getLogger(__name__)

class ObservationTableView(HTMXTableViewMixin, ListView):
    table_class = ObservationTable
    template_name = "tom_across/observation_table.html"
    paginate_by = 10
    model = None

    def get_queryset(self):
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
                'obs_type': form.cleaned_data.get('observation_type'),
                'cone_search_radius': form.cleaned_data.get('cone_radius'),
            }
            filters = {k: v for k, v in filters.items() if v not in (None, '')}
        return observation_rows(target, **filters)

    def get_context_data(self, **kwargs):
        context = super(HTMXTableViewMixin, self).get_context_data(**kwargs)
        context['record_count'] = context['paginator'].count
        context['empty_database'] = not context['object_list']
        context['target'] = Target.objects.get(id=self.kwargs['target_id'])
        context['filter_form'] = ObservationFilterForm(self.request.GET or None)
        return context

def visibility_plot_view(request, pk):
    target = Target.objects.get(id=pk)
    if target.type != 'SIDEREAL':
        return render(request, 'tom_across/partials/visibility_plot.html', {'plot': None})
    
    names = sorted(set(get_observatory_name_id_map().values()))
    observatory_choices = [(n, n) for n in names]
    now = datetime.now()
    default_observatories = getattr(settings, 'ACROSS_VIS_OBSERVATORIES', ['HST', 'JWST'])
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

    context = visibility_from_instrument(target, observatory_list, date_range_begin = date_range_begin, date_range_end = date_range_end)
    context['form'] = form
    return render(request, 'tom_across/partials/visibility_plot.html', context)
