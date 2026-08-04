import django_tables2 as tables
from tom_common.htmx_table import HTMXTable
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)
class ObservationTable(HTMXTable):
    telescope = tables.Column()
    instrument = tables.Column()
    exptime = tables.Column()
    date = tables.DateTimeColumn(format="Y-m-d H:i")
    type = tables.Column()
    filter_name = tables.Column()
    wavelength_range = tables.Column()
    status = tables.Column()

    selection = None

    class Meta(HTMXTable.Meta):
        model = None
        empty_text = "No observations found"
        attrs = {
            **HTMXTable.Meta.attrs,
            "hx-target": "#observation-table-wrapper",
            "hx-swap": "outerHTML",
        }
    
    partial_template_name = 'tom_across/partials/observation_table_partial.html'

    def get_table_action_url(self):
        target_id = self.request.resolver_match.kwargs.get("target_id")
        return reverse("across:observation-table", kwargs={"target_id": target_id})

    def render_exptime(self, value):
        try:
            return f"{float(value):.1f}"
        except (ValueError, TypeError):
            return value

    def render_wavelength_range(self, value):
            try:
                rendered_min = f"{float(value[0]):.0f}" if float(value[0]) > 1 else f"{float(value[0]):.2e}"
                rendered_max = f"{float(value[1]):.0f}" if float(value[1]) > 1 else f"{float(value[1]):.2e}"
                return f"{rendered_min} - {rendered_max}"
            except (ValueError, TypeError):
                return value
