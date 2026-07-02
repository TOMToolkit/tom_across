import django_tables2 as tables

class ObservationTable(tables.Table):
    telescope = tables.Column()
    instrument = tables.Column()
    exptime = tables.Column()
    date = tables.DateTimeColumn(format="Y-m-d H:i")
    type = tables.Column()
    filter_name = tables.Column()
    wavelength_range = tables.Column()


    class Meta:
        template_name = "tom_across/observation_table.html"
        orderable = True
        attrs = {
            "class": "table table-striped table-hover",
            "id": "observation-table",
        }
        empty_text = "No observations found"

    def render_exptime(self, value):
        return f"{value:.2f}"