from urllib.parse import urlencode
from django import template

register = template.Library()

@register.inclusion_tag('tom_across/partials/observation_table.html', takes_context=True)
def observation_table(context):
    return {'test': 'ACROSS TEST'}