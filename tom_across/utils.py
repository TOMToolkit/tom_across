from django.core.cache import cache

import logging

logger = logging.getLogger(__name__)

def observation_rows(client, target):
    results = client.observation.get_many(
        status="performed",
        cone_search_ra=target.ra,
        cone_search_dec=target.dec,
        cone_search_radius=0.01,
    )

    instrument_cache = get_across_instrument_ids(client)
    rows = []

    for obs in results.items:
        inst,tele = instrument_cache[obs.instrument_id]
        logger.info(f'instrument from cache: {inst}, {tele}')
        
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
    logger.info(f'TESTROWS: {rows}')
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

