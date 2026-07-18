import json
from datetime import datetime, timedelta, timezone
from itertools import combinations

from django.core.cache import cache
from django.shortcuts import render, get_object_or_404
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
from tom_across.utils import observation_rows
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

def get_observatory_choices():
    cache_key = "across_observatory_choices"
    choices = cache.get(cache_key)
    if choices is None:
        client = Client()
        observatories = client.observatory.get_many()
        choices = sorted([(o.short_name, o.short_name) for o in observatories])
        cache.set(cache_key, choices, timeout=3600)
    return choices

def visibility_plot_view(request, pk):
    target = get_object_or_404(Target, pk=pk)
    if target.type != 'SIDEREAL':
        return render(request, 'tom_across/partials/visibility_plot.html', {'plot': None})

    observatory_choices = get_observatory_choices()
    now = datetime.now()
    defaults = {'observatories': ['HST', 'JWST', 'Swift'], 'begin': now, 'end': now + timedelta(hours=24)}
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

    now = date_range_begin  # hours are measured from range start, not wall-clock now
    day_range_hours = (date_range_end - date_range_begin).total_seconds() / 3600

    cache_key = (f"visibility_plot_{target.id}_{'_'.join(sorted(observatory_list))}_"
                 f"{date_range_begin.isoformat()}_{date_range_end.isoformat()}")
    cached_context = cache.get(cache_key)
    if cached_context:
        context = {**cached_context, 'form': form, 'target': target}
        return render(request, 'tom_across/partials/visibility_plot.html', context)
    client = Client()
    ra, dec = target.ra, target.dec

    joint_instrument_ids = []
    inst_id_by_name = {}
    for obs_name in observatory_list:
        instruments = client.instrument.get_many(name=obs_name)
        for inst in instruments[:1]:
            joint_instrument_ids.append(inst.id)
            inst_id_by_name[obs_name] = inst.id

    joint = client.visibility_calculator.calculate_joint_windows(
        instrument_ids=joint_instrument_ids, ra=ra, dec=dec,
        date_range_begin=date_range_begin, date_range_end=date_range_end
    )

    observatory_name_cache = {}
    for inst_id in joint_instrument_ids:
        for ovw in joint.observatory_visibility_windows[inst_id]:
            oid = ovw.window.end.observatory_id
            if oid not in observatory_name_cache:
                observatory_name_cache[oid] = client.observatory.get(oid).short_name
    for jvw in joint.visibility_windows:
        oid = jvw.window.end.observatory_id
        if oid not in observatory_name_cache:
            observatory_name_cache[oid] = client.observatory.get(oid).short_name

    def compute_joint(selected_ids):
        if len(selected_ids) < 2:
            return None
        result = client.visibility_calculator.calculate_joint_windows(
            instrument_ids=selected_ids, ra=ra, dec=dec,
            date_range_begin=date_range_begin, date_range_end=date_range_end
        )
        for jvw in result.visibility_windows:
            oid = jvw.window.end.observatory_id
            if oid not in observatory_name_cache:
                observatory_name_cache[oid] = client.observatory.get(oid).short_name
        return result.visibility_windows

    joint_cache = {}
    for r in range(2, len(joint_instrument_ids) + 1):
        for combo in combinations(joint_instrument_ids, r):
            joint_cache[frozenset(combo)] = compute_joint(list(combo))

    def build_fig(selected_names):
        selected_ids = [inst_id_by_name[name] for name in selected_names]
        if not selected_ids:
            return go.Figure()

        fig = make_subplots(rows=len(selected_ids), cols=1, shared_xaxes=True, vertical_spacing=0)

        color = ["#4C9CA8", "#B7E1E7"]
        legend_added = {"obs": False, "joint": False}
        for i, inst_id in enumerate(selected_ids):
            obs_vis_windows = joint.observatory_visibility_windows[inst_id]
            for obs_vis_window in obs_vis_windows:
                observatory_max_vis = obs_vis_window.max_visibility_duration
                observatory_window = obs_vis_window.window
                observatory_begin_hours = (observatory_window.begin.datetime - now).total_seconds()/3600 if (observatory_window.begin.datetime - now).total_seconds() > 0 else 0
                observatory_end_hours = (observatory_window.end.datetime - now).total_seconds()/3600 if (observatory_window.end.datetime - now).total_seconds() > 0 else 0
                observatory_name = observatory_name_cache[observatory_window.end.observatory_id]

                fig.add_trace(go.Scatter(
                    x=[observatory_begin_hours, observatory_end_hours, observatory_end_hours, observatory_begin_hours, observatory_begin_hours],
                    y=[0, 0, 1, 1, 0],
                    fill="toself",
                    fillcolor=color[1],
                    line=dict(color=color[0], width=3),
                    opacity=0.5,
                    mode="lines",
                    hoverinfo="text",
                    text=f"{observatory_name}<br>{observatory_window.begin.datetime}–{observatory_window.end.datetime}<br>Max vis: {observatory_max_vis}",
                    name="Observatory Visibility Window",
                    legendgroup="obs",
                    showlegend=not legend_added["obs"],
                ), row=i+1, col=1)
                legend_added["obs"] = True
            fig.update_yaxes(title_text=observatory_name, showgrid=False, showticklabels=False, range=[0, 1], row=i+1, col=1)

        color = ["#E783D5", "#EBCEE6"]
        joint_windows_for_selection = joint_cache.get(frozenset(selected_ids))
        if joint_windows_for_selection:
            for jvw in joint_windows_for_selection:
                max_vis = jvw.max_visibility_duration
                joint_window = jvw.window
                joint_begin_hours = (joint_window.begin.datetime - now).total_seconds()/3600 if (joint_window.begin.datetime - now).total_seconds() > 0 else 0
                joint_end_hours = (joint_window.end.datetime - now).total_seconds()/3600 if (joint_window.end.datetime - now).total_seconds() > 0 else 0

                for row in range(len(selected_ids)):
                    fig.add_trace(go.Scatter(
                        x=[joint_begin_hours, joint_end_hours, joint_end_hours, joint_begin_hours, joint_begin_hours],
                        y=[0, 0, 1, 1, 0],
                        fill="toself",
                        fillcolor=color[1],
                        line=dict(color=color[0], width=3),
                        opacity=0.5,
                        mode="lines",
                        hoverinfo="text",
                        text=f"Joint window<br>{joint_window.begin.datetime}–{joint_window.end.datetime}<br>Max vis: {max_vis}",
                        name="Joint Visibility Window",
                        legendgroup="joint",
                        showlegend=not legend_added["joint"],
                    ), row=row+1, col=1)
                    legend_added["joint"] = True

        fig.update_xaxes(range=[0, day_range_hours])
        fig.update_xaxes(title_text="Hours from range start", row=len(selected_ids))
        fig.update_layout(
            height=150 * len(selected_ids) + 100,
            autosize=True,
            showlegend=True,
            legend=dict(
                groupclick="togglegroup", orientation="h", yanchor="bottom", y=1.02,
                xanchor="left", x=0, font=dict(size=14),
            ),
            font=dict(size=14),
            margin=dict(t=60),
        )
        return fig

    figures_by_combo = []
    for r in range(1, len(observatory_list) + 1):
        for combo in combinations(observatory_list, r):
            key = ",".join(sorted(combo))
            fig = build_fig(list(combo))
            figures_by_combo.append((key, offline.plot(fig, output_type='div', show_link=False, config={'responsive': True})))

    context = {
        'form': form,
        'target': target,
        'observatory_list': observatory_list,
        'figures_by_combo': figures_by_combo,
    }
    cacheable_context = {
        'observatory_list': observatory_list,
        'figures_by_combo': figures_by_combo,
    }
    cache.set(cache_key, cacheable_context, timeout=300)

    context = {**cacheable_context, 'form': form, 'target': target}
    return render(request, 'tom_across/partials/visibility_plot.html', context)

class AcrossDashboardView(TemplateView):
    template_name = "tom_across/dashboard.html"