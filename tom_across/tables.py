import django_tables2 as tables
from tom_common.htmx_table import HTMXTable
from django.urls import reverse

class ObservationTable(HTMXTable):
    telescope = tables.Column()
    instrument = tables.Column()
    exptime = tables.Column()
    date = tables.DateTimeColumn(format="Y-m-d H:i")
    type = tables.Column()
    filter_name = tables.Column()
    wavelength_range = tables.Column()

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
            return f"{float(value):.2f}"
        except (ValueError, TypeError):
            return value
