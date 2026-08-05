from django.core.cache import cache
from datetime import datetime, timedelta
from plotly import graph_objs as go
from plotly.io import to_html
from plotly.subplots import make_subplots
from across.sdk.v1.exceptions import ServiceException
import hashlib
from django.conf import settings
from across.client import Client
import logging

client = Client()
logger = logging.getLogger(__name__)

ACROSS_OBSERVATION_DEFAULT_ARGS = {'status': 'planned', 'cone_search_radius': 0.1}


def visibility_from_instrument(target, observatory_list, date_range_begin=None, date_range_end=None, hi_res=True):

    ra, dec = target.ra, target.dec
    obs_names_to_instr_ids = get_inst_ids_from_observatory_name()

    selected_observatories = [
        (name, obs_names_to_instr_ids[name])
        for name in observatory_list if name in obs_names_to_instr_ids
        ]

    inst_ids = [inst_id for _, inst_id in selected_observatories]

    if date_range_begin is None:
        date_range_begin = datetime.now()

    if date_range_end is None:
        date_range_end = date_range_begin + timedelta(hours=24)

    cache_key = (f"visibility_plot_{target.id}_{'_'.join(sorted(observatory_list))}_"
                 f"{date_range_begin.isoformat()}"
                 f"_{date_range_end.isoformat()}")
    cached_context = cache.get(cache_key)
    if cached_context:
        logger.info('[VISIBILITY] Pulling from cache')
        return {**cached_context, 'target': target}

    joint = client.visibility_calculator.calculate_joint_windows(
        instrument_ids=inst_ids, ra=ra, dec=dec,
        date_range_begin=date_range_begin, date_range_end=date_range_end,
        hi_res=hi_res
        )

    observatory_name_cache = get_observatory_name_id_map()

    fig = make_subplots(rows=len(inst_ids), cols=1, shared_xaxes=True, vertical_spacing=0)
    color = ["#4C9CA8", "#B7E1E7"]

    for i, (selected_name, inst_id) in enumerate(selected_observatories):
        obs_vis_windows = joint.observatory_visibility_windows[inst_id]
        observatory_name = selected_name
        for obs_vis_window in obs_vis_windows:
            observatory_max_vis = obs_vis_window.max_visibility_duration
            observatory_window = obs_vis_window.window
            observatory_name = observatory_name_cache[observatory_window.end.observatory_id]
            fig.add_trace(
                go.Scatter(
                    x=[
                        observatory_window.begin.datetime,
                        observatory_window.end.datetime,
                        observatory_window.end.datetime,
                        observatory_window.begin.datetime,
                        observatory_window.begin.datetime
                    ],
                    y=[0, 0, 1, 1, 0],
                    fill="toself",
                    fillcolor=color[1],
                    line=dict(color=color[0], width=3),
                    opacity=0.5,
                    mode="lines",
                    hoverinfo="text",
                    text=f"{observatory_name}<br>{observatory_window.begin.datetime}"
                         f" – {observatory_window.end.datetime}"
                         f"<br>Max Visibility: {observatory_max_vis/3600:0.2f} Hours",
                    showlegend=False
                ),
                row=i+1,
                col=1
            )

        if not obs_vis_windows:
            fig.add_trace(go.Scatter(
                x=[date_range_begin, date_range_end], y=[0, 0],
                mode="lines",
                line=dict(color="rgba(0,0,0,0)"),
                hoverinfo="skip",
                showlegend=False,
            ), row=i + 1, col=1)

        fig.update_yaxes(
            title_text=observatory_name, showgrid=False, showticklabels=False, range=[0, 1], row=i+1, col=1
            )

    fig.update_xaxes(range=[date_range_begin, date_range_end])
    fig.update_layout(
        height=150 * len(inst_ids) + 100,
        autosize=True,
        showlegend=False,
        margin=dict(t=40),
        font=dict(size=14),
    )

    plot_html = to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True})

    cacheable_context = {
        'observatory_list': observatory_list,
        'plot_html': plot_html,
    }
    cache.set(cache_key, cacheable_context, timeout=300)

    return {**cacheable_context, 'target': target}


def get_observatory_name_id_map():
    """
    Build name/short_name to observatory_id map.
    Cached for 24 hours, refreshed on cache miss.
    """
    cache_key = "across_observatory_id_name_map"
    data = cache.get(cache_key)
    if data is None:
        print('GETTING OBS IDS TO FROM ACROSS')
        data = {o.id: o.short_name for o in client.observatory.get_many()}
        cache.set(cache_key, data, timeout=24 * 60 * 60)
    return data


def get_inst_ids_from_observatory_name():
    """
    Build unique name/short_name list for observatory,
    telescope, and instrument to instrument_id map.
    Cached for 24 hours, refreshed on cache miss.
    """
    cache_key = "across_instrument_id_observatory_map"
    data = cache.get(cache_key)

    if data is None:
        print('MAPPING INST IDS TO OBSERVATORIES')
        data = {}
        observatories = client.observatory.get_many()

        for obs in observatories:
            obs_names = [obs.name, obs.short_name]
            for tele in obs.telescopes:
                tele = client.telescope.get(tele.id)
                tele_names = [tele.name, tele.short_name]
                for inst in tele.instruments:
                    names = set(obs_names + tele_names + [inst.name, inst.short_name])
                    for name in names:
                        data[name] = inst.id

        cache.set(cache_key, data, timeout=24 * 60 * 60)

    return data


def observation_rows(target, start_date=None, end_date=None, status=None, instrument=None,
                       obs_type=None, cone_search_radius=None):
    kwargs = getattr(settings, 'ACROSS_OBSERVATION_DEFAULT_ARGS', ACROSS_OBSERVATION_DEFAULT_ARGS).copy()
    instrument_cache = get_across_instrument_ids()

    if target.type == "SIDEREAL":        
        kwargs['cone_search_ra'] = target.ra
        kwargs['cone_search_dec'] = target.dec
        cone_search_from_settings = kwargs.get("cone_search_radius")
        if not cone_search_from_settings:
            kwargs["cone_search_radius"] = 0.1

    if start_date:
        kwargs['date_range_begin'] = start_date
    if end_date:
        kwargs['date_range_end'] = end_date
    if status:
        kwargs['status'] = status
    inst_id = None
    if instrument:
        for key, value_list in instrument_cache.items():
            if instrument in value_list:
                inst_id = key
                kwargs['instrument_ids'] = [inst_id]
    if obs_type:
        kwargs['type'] = obs_type
    if cone_search_radius:
        kwargs['cone_search_radius'] = cone_search_radius

    key_raw = (
        f"{target.id}-{start_date}-{end_date}-{status}-"
        f"{inst_id}-{obs_type}-{cone_search_radius}"
        )

    cache_key = "across_obs_" + hashlib.md5(key_raw.encode()).hexdigest()
    rows = cache.get(cache_key)
    if rows:
        logger.info(f'[OBSERVATION TABLE] Pulling from cache with key {key_raw}')
        return rows
    rows = []
    try:
        results = client.observation.get_many(**kwargs)
        for obs in results.items:
            inst, tele = instrument_cache[obs.instrument_id]

            obs_tele_name_dict = get_across_observatory_telescope_name_map()
            for obs_name, tele_names in obs_tele_name_dict.items():
                if tele in tele_names:
                    break

            band = obs.bandpass.to_dict().get('filter_name')
            min_band = obs.bandpass.to_dict().get('min')
            max_band = obs.bandpass.to_dict().get('max')
            status = obs.status.value
            proposal = obs.proposal_reference
            
            rows.append({
                'observatory': obs_name,
                'instrument': inst,
                'exptime': obs.exposure_time,
                'date': obs.date_range.end,
                'status':status,
                'type': getattr(obs.type, 'value', obs.type),
                'filter_name': band,
                'wavelength_range': (min_band, max_band),
                'proposal': proposal,
            })

    except ServiceException as e:
        logger.info(f'Loading error: {e}')

    cache.set(cache_key, rows, timeout=24 * 60 * 60)
    return rows


def get_across_instrument_ids():
    """
    Build a dictionary of ACROSS instrument IDs and their corresponding names.
    This is used to look up instruments by ID on other requests to the ACROSS API.
    Cached for 24 hours, refreshed on cache miss.
    """
    cache_key = "across_instrument_id_map"
    data = cache.get(cache_key)

    if data is None:
        print('GETTING INST IDS FROM ACROSS')
        instruments = client.instrument.get_many()
        data = {instrument.id: [instrument.name, instrument.telescope.name] for instrument in instruments}

        cache.set(cache_key, data, timeout=24 * 60 * 60)  # Cache for 24 hours

    return data

def get_across_observatory_telescope_name_map():
    """
    Build a dictionary of ACROSS observatory names and their corresponding telescope names.
    Cached for 24 hours, refreshed on cache miss.
    """
    cache_key = "across_observatory_telescope_name_map"
    data = cache.get(cache_key)

    if data is None:
        print('GETTING OBSERVATORY TELESCOPE NAMES FROM ACROSS')
        observatories = client.observatory.get_many()
        data = {}
        for obs in observatories:
            data[obs.short_name] = [tele.name for tele in obs.telescopes]

        cache.set(cache_key, data, timeout=24 * 60 * 60)  # Cache for 24 hours

    return data

def get_across_observatory_telescope_name_map():
    """
    Build a dictionary of ACROSS observatory names and their corresponding telescope names.
    Cached for 24 hours, refreshed on cache miss.
    """
    cache_key = "across_observatory_telescope_name_map"
    data = cache.get(cache_key)

    if data is None:
        print('GETTING OBSERVATORY TELESCOPE NAMES FROM ACROSS')
        observatories = client.observatory.get_many()
        data = {}
        for obs in observatories:
            data[obs.short_name] = [tele.name for tele in obs.telescopes]

        cache.set(cache_key, data, timeout=24 * 60 * 60)  # Cache for 24 hours

    return data
