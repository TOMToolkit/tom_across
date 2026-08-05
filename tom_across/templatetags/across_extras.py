from urllib.parse import urlencode
from django import template
from django.conf import settings
from tom_across import __version__

register = template.Library()

DEFAULT_ACROSS_APP_URL = 'https://app.across.sciencecloud.nasa.gov'
DEFAULT_CONE_SEARCH_RADIUS = 0.1


@register.simple_tag
def across_app_visibility_url(target, hi_res=True):
    base = getattr(settings, 'ACROSS_APP_URL', DEFAULT_ACROSS_APP_URL)
    query = urlencode({
        'ra': f'{target.ra:f}',
        'dec': f'{target.dec:f}',
        'hi_res': str(hi_res).lower(),
    })
    return f'{base}/visibility-calculator?{query}'


@register.simple_tag
def across_app_observations_url(target, radius=DEFAULT_CONE_SEARCH_RADIUS):
    base = getattr(settings, 'ACROSS_APP_URL', DEFAULT_ACROSS_APP_URL)
    across_defaults = getattr(settings, 'ACROSS_DEFAULT_ARGS', None) or {}
    obs_defaults = across_defaults.get('OBSERVATION_TABLE_DEFAULTS') or {}
    query = urlencode({
        'cone_search_ra': f'{target.ra:f}',
        'cone_search_dec': f'{target.dec:f}',
        'cone_search_radius': obs_defaults.get('cone_search_radius', radius),
    })
    return f'{base}/observations?{query}'

@register.inclusion_tag('tom_across/target_across.html', takes_context=True)
def version_context(context):
    context = {'version': __version__}
    return context
