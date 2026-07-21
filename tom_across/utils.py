from django.core.cache import cache
from across.sdk.v1.exceptions import ServiceException
import json
import logging
from importlib import resources
import hashlib
from datetime import datetime, timedelta
from itertools import combinations
from plotly import graph_objs as go
from plotly import offline
from plotly.subplots import make_subplots


logger = logging.getLogger(__name__)

def observation_rows(client, target, start_date=None, end_date=None, wavelength_type=None,
                      wavelength_min=None, wavelength_max=None, obs_type=None):
    kwargs = dict(
        status="planned",
        cone_search_ra=target.ra,
        cone_search_dec=target.dec,
        cone_search_radius=0.01,
    )
    if start_date:
        kwargs['date_range_begin'] = start_date
    if end_date:
        kwargs['date_range_end'] = end_date
    if wavelength_type:
        kwargs['bandpass_type'] = wavelength_type
    if wavelength_min:
        kwargs['bandpass_min'] = wavelength_min
    if wavelength_max:
        kwargs['bandpass_max'] = wavelength_max
    if obs_type:
        kwargs['type'] = obs_type

    logger.info(f'kwargs: {kwargs}')
    key_raw = f"{target.id}-{start_date}-{end_date}-{wavelength_min}-{wavelength_max}-{wavelength_type}-{obs_type}"
    cache_key = "across_obs_" + hashlib.md5(key_raw.encode()).hexdigest()
    rows = cache.get(cache_key)
    if rows is not None:
        return rows

    rows = []
    try:
        results = client.observation.get_many(**kwargs)

        
        instrument_cache = get_across_instrument_ids(client)
        for obs in results.items:
            inst, tele = instrument_cache[obs.instrument_id]
            band = obs.bandpass.to_dict().get('filter_name')
            min_band = obs.bandpass.to_dict().get('min')
            max_band = obs.bandpass.to_dict().get('max')
            rows.append({
                'telescope': tele,
                'instrument': inst,
                'exptime': obs.exposure_time,
                'date': obs.date_range.end,
                'type': getattr(obs.type, 'value', obs.type),
                'filter_name': band,
                'wavelength_range': f'{min_band} - {max_band}'
            })
    except ServiceException as e:
        if "504" in str(e) or "Gateway Timeout" in str(e):
            with resources.open_text('tom_across.test_files', 'test_response.json') as file:
                rows = json.load(file)
        else:
            logger.info(f'Other error: {e}')

    cache.set(cache_key, rows, timeout=24 * 60 * 60)
    return rows

def visibility_from_instrument(target, client, observatory_list, date_range_begin=datetime.now(), date_range_end=datetime.now() + timedelta(hours=24)):

    ra, dec = target.ra, target.dec
    logger.info('getting instrument observatory name cache')
    obs_names_to_instr_ids = get_inst_ids_from_observatory_name(client)
    inst_ids = [obs_names_to_instr_ids[name] for name in observatory_list if name in obs_names_to_instr_ids]
    logger.info('gotten')

    now = date_range_begin
    day_range_hours = (date_range_end - date_range_begin).total_seconds() / 3600

    logger.info('does cache exist?')
    cache_key = (f"visibility_plot_{target.id}_{'_'.join(sorted(observatory_list))}_{date_range_begin.isoformat()}_{date_range_end.isoformat()}")
    cached_context = cache.get(cache_key)
    logger.info(f'cache_key: {cache_key}')
    if cached_context:
        return {**cached_context, 'target': target}

    logger.info(f'instrument ids {inst_ids}, ra {ra}, dec {dec}, date_range_begin {date_range_begin}, date_range_end {date_range_end}')
    joint = client.visibility_calculator.calculate_joint_windows(instrument_ids=inst_ids, ra=ra, dec=dec, date_range_begin=date_range_begin, date_range_end=date_range_end)
    observatory_name_cache = get_observatory_name_id_map(client)

    fig = make_subplots(rows=len(inst_ids), cols=1, shared_xaxes=True, vertical_spacing=0)
    color = ["#4C9CA8", "#B7E1E7"]

    for i, inst_id in enumerate(inst_ids):
        obs_vis_windows = joint.observatory_visibility_windows[inst_id]
        observatory_name = None
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
                text=f"{observatory_name}<br>{observatory_window.begin.datetime} – {observatory_window.end.datetime}<br>Max Visibility: {observatory_max_vis/3600:0.2f} Hours",
                showlegend=False,
            ), row=i+1, col=1)

        fig.update_yaxes(title_text=observatory_name, showgrid=False, showticklabels=False, range=[0, 1], row=i+1, col=1)

    fig.update_xaxes(range=[0, day_range_hours])
    fig.update_xaxes(title_text=f"Hours from {date_range_begin.strftime('%B %d, %Y %I:%M %p')}", row=len(inst_ids))
    fig.update_layout(
        height=150 * len(inst_ids) + 100,
        autosize=True,
        showlegend=False,
        margin=dict(t=40),
        font=dict(size=14),
    )

    plot_html = offline.plot(fig, output_type='div', show_link=False, config={'responsive': True})

    cacheable_context = {
        'observatory_list': observatory_list,
        'plot_html': plot_html,
    }
    cache.set(cache_key, cacheable_context, timeout=300)

    return {**cacheable_context, 'target': target}

def get_observatory_name_id_map(client):
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

def get_inst_ids_from_observatory_name(client):
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

def get_across_instrument_ids(client):
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
        data = {instrument.id: [instrument.name,instrument.telescope.name] for instrument in instruments}

        cache.set(cache_key, data, timeout=24 * 60 * 60)  # Cache for 24 hours

    return data