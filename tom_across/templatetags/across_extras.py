from urllib.parse import urlencode
from django import template
from datetime import datetime, timedelta
from plotly import graph_objs as go
import json
from itertools import combinations
from plotly.subplots import make_subplots
from plotly import offline
from across.client import Client

import logging

logger = logging.getLogger(__name__)

register = template.Library()

@register.inclusion_tag('tom_across/partials/visibility_plot.html')
def visibility_plot(target, observatory_list=None, day_range=30, width=600, height=400, background=None, label_color=None, grid=True):

    if target.type != 'SIDEREAL':
        return {'plot': None}

    observatory_list = observatory_list or ['HST', 'JWST', 'Swift']
    now = datetime.now()
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
        date_range_begin=now, date_range_end=now + timedelta(hours=24 * day_range)
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
            date_range_begin=now, date_range_end=now + timedelta(hours=24 * day_range)
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

        fig.update_xaxes(range=[0, 24 * day_range])
        fig.update_xaxes(title_text="Hours from now", row=len(selected_ids))
        fig.update_layout(height=150 * len(selected_ids) + 100, width=600, showlegend=True, legend=dict(groupclick="togglegroup"))
        return fig

    # precompute a div for every non-empty combo, keyed by sorted comma-joined names
    figures_by_combo = {}
    for r in range(1, len(observatory_list) + 1):
        for combo in combinations(observatory_list, r):
            key = ",".join(sorted(combo))
            fig = build_fig(list(combo))
            figures_by_combo[key] = offline.plot(fig, output_type='div', show_link=False)

    return {
        'observatory_list': observatory_list,
        'figures_by_combo_json': json.dumps(figures_by_combo),
    }