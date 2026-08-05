from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, HTML, Field
from datetime import datetime, timedelta

import logging

logger = logging.getLogger(__name__)


class ObservationFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
        )
    end_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
        )
    observation_type = forms.CharField(required=False, label='Observation type', widget=forms.Select())
    instrument = forms.CharField(required=False, label='Instrument', widget=forms.Select())
    status = forms.CharField(required=False, label='Observation Status', widget=forms.Select())
    cone_radius = forms.FloatField(required=False, label='Cone Radius')

    def __init__(self, *args, **kwargs):
        qs_data = kwargs.pop('queryset_data', None)
        super().__init__(*args, **kwargs)

        if qs_data:
            unique_instruments = sorted(list({row['instrument'] for row in qs_data if row.get('instrument')}))
            self.fields['instrument'].widget.choices = [('', 'Any')] + [(inst, inst) for inst in unique_instruments]

            unique_types = sorted(list({row['type'] for row in qs_data if row.get('type')}))
            self.fields['observation_type'].widget.choices = [('', 'Any')] + [(t, t.capitalize()) for t in unique_types]

            unique_statuses = sorted(list({row['status'] for row in qs_data if row.get('status')}))
            self.fields['status'].widget.choices = [('', 'Any')] + [(s, s.capitalize()) for s in unique_statuses]

            all_dates = [
                row['date'].date()
                if isinstance(row['date'], datetime)
                else row['date'] for row in qs_data if row.get('date')
            ]

            min_date = min(all_dates) - timedelta(days=1)   # add buffer for not including time
            max_date = max(all_dates) + timedelta(days=1)   # add buffer for not including time

            self.fields['start_date'].initial = min_date
            self.fields['end_date'].initial = max_date
            if self.is_bound:
                if not self.data.get('start_date'):
                    self.fields['start_date'].widget.value_from_datadict = lambda *args, **kwargs: min_date.isoformat()
                if not self.data.get('end_date'):
                    self.fields['end_date'].widget.value_from_datadict = lambda *args, **kwargs: max_date.isoformat()

        else:
            self.fields['instrument'].choices = [('', 'Any')]
            self.fields['observation_type'].choices = [('', 'Any')]

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            Row(
                Column('start_date', css_class='form-group col-md-6 mb-0'),
                Column('end_date', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('observation_type', css_class='col-md-4'),
                Column('instrument', css_class='col-md-4'),
                Column('status', css_class='col-md-4'),
                Column('cone_radius', css_class='col-md-4'),
                Column(
                    HTML(
                        '<button type="submit" class="btn btn-outline-primary w-100">'
                        'Filter</button>'
                    ),
                    css_class='col-md-4 d-flex align-items-end mb-3'
                ),
                css_class='row g-3'
            ),
        )


class VisibilityPlotForm(forms.Form):
    observatories = forms.MultipleChoiceField(
        required=True, widget=forms.CheckboxSelectMultiple, label=False
        )
    begin = forms.DateTimeField(
        required=True, widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label='Begin (UTC)'
        )
    end = forms.DateTimeField(
        required=True, widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label='End (UTC)'
        )

    def __init__(self, *args, observatory_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['observatories'].choices = observatory_choices or []

        self.helper = FormHelper()
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Row(
                Column('begin', css_class='col-md-4'),
                Column('end', css_class='col-md-4'),
                Column(
                    HTML(
                        '<button id="update-btn" type="submit" class="btn btn-primary w-100">'
                        'Update <span id="plot-spinner"'
                        'class="htmx-indicator spinner-border spinner-border-sm ms-1" role="status"></span>'
                        '</button>'
                    ),
                    css_class='col-md-4 d-flex align-items-end mb-3'
                ),
                css_class='row g-3'
            ),
            HTML(
                '<details class="mb-4 card card-body py-2 px-3">'
                '<summary class="cursor-pointer">Observatories</summary>'
                '<div class="mt-2">'
            ),
            Field('observatories', css_class='row row-cols-1 row-cols-md-3'),
            HTML('</div></details>'),
        )
