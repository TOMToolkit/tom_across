from django.core.cache import cache
from across.sdk.v1.exceptions import ServiceException
import json
import logging
from importlib import resources
import hashlib

logger = logging.getLogger(__name__)

def observation_rows(client, target, start_date=None, end_date=None,
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
    if wavelength_min:
        kwargs['bandpass_min'] = wavelength_min
    if wavelength_max:
        kwargs['bandpass_max'] = wavelength_max
    if obs_type:
        kwargs['type'] = obs_type
    key_raw = f"{target.id}-{start_date}-{end_date}-{wavelength_min}-{wavelength_max}-{obs_type}"
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

def get_across_instrument_ids(client) -> dict:
    """
    Build a dictionary of ACROSS instrument IDs and their corresponding names.
    This is used to look up instruments by ID on other requests to the ACROSS API.
    This will be cached for 24 hours and refreshed on cache miss.
    """
    cache_key = "across_instrument_id_map"
    data = cache.get(cache_key)

    if data is None:
        print('GETTING INST IDS FROM ACROSS')
        instruments = client.instrument.get_many()
        data = {instrument.id: [instrument.name,instrument.telescope.name] for instrument in instruments}

        cache.set(cache_key, data, timeout=24 * 60 * 60)  # Cache for 24 hours

    return data