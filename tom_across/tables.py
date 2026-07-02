import django_tables2 as tables
from tom_common.htmx_table import HTMXTable

class ObservationTable(HTMXTable):
    telescope = tables.Column()
    instrument = tables.Column()
    exptime = tables.Column()
    date = tables.DateTimeColumn(format="Y-m-d H:i")
    type = tables.Column()
    filter_name = tables.Column()
    wavelength_range = tables.Column()

    class Meta(HTMXTable.Meta):
        empty_text = "No observations found"

    def render_exptime(self, value):
        return f"{value:.2f}"