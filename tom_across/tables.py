import django_tables2 as tables
from tom_common.htmx_table import HTMXTable
from django.urls import reverse
from django.utils.html import format_html
import logging

logger = logging.getLogger(__name__)


class ObservationTable(HTMXTable):
    observatory = tables.Column()
    type = tables.Column()
    date = tables.DateTimeColumn(format='Y-m-d H:i')
    filter_name = tables.Column(verbose_name='Filter')
    exptime = tables.Column(verbose_name='Exp (s)', attrs={'th': {'class': 'text-nowrap'}})
    status = tables.Column()

    selection = None

    class Meta(HTMXTable.Meta):
        model = None
        empty_text = 'No observations found'
        attrs = {
            **HTMXTable.Meta.attrs,
            'hx-target': '#observation-table-wrapper',
            'hx-swap': 'outerHTML'
        }

    partial_template_name = 'tom_across/partials/observation_table_partial.html'

    def get_table_action_url(self):
        target_id = self.request.resolver_match.kwargs.get('target_id')
        return reverse('tom_across:observation-table', kwargs={'target_id': target_id})

    def render_observatory(self, value, record):
        instrument = record.get('instrument') if isinstance(record, dict) else getattr(record, 'instrument', None)
        if instrument:
            return format_html('{}<br><small class="text-muted">{}</small>', value, instrument)
        return value

    def render_exptime(self, value):
        try:
            return f'{float(value):.1f}'
        except (ValueError, TypeError):
            return value
