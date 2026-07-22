from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.shortcuts import render

from tom_targets.models import Target
from tom_across.forms import VisibilityPlotForm
from tom_across.utils import get_observatory_name_id_map, visibility_from_instrument
import logging

logger = logging.getLogger(__name__)

def visibility_plot_view(request, pk):
    target = Target.objects.get(id=pk)
    if target.type != 'SIDEREAL':
        return render(request, 'tom_across/partials/visibility_plot.html', {'plot': None})
    
    names = sorted(set(get_observatory_name_id_map().values()))
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

    context = visibility_from_instrument(target, observatory_list, date_range_begin = date_range_begin, date_range_end = date_range_end)
    context['form'] = form
    return render(request, 'tom_across/partials/visibility_plot.html', context)
