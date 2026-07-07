from django.core.cache import cache
from across.sdk.v1.exceptions import ServiceException
import json
import logging
from importlib import resources

logger = logging.getLogger(__name__)

def observation_rows(client, target):
    try:
        results = client.observation.get_many(
            status="planned",
            cone_search_ra=target.ra,
            cone_search_dec=target.dec,
            cone_search_radius=0.01,
        )
        logger.info(f'Client responded')
        instrument_cache = get_across_instrument_ids(client)
        rows = []
        
        for obs in results.items:
            inst,tele = instrument_cache[obs.instrument_id]
            
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
            rows.append(obs)

    except ServiceException as e:
        if "504" in str(e) or "Gateway Timeout" in str(e):
            logger.info(f'Gateway timeout, opening file')
            with resources.open_text('tom_across.test_files', 'test_response.json') as file:
                rows = json.load(file)
        else:
            logger.info(f'Other error: {e}')
            pass
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

