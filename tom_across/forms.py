from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, HTML, Field

import logging

logger = logging.getLogger(__name__)

WAVELENGTH_TYPE_CHOICES = [
    ('angstrom', 'angstrom'),
    ('nm', 'nm'),
    ('keV', 'keV'),
]


class ObservationFilterForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    wavelength_type = forms.ChoiceField(required=False, label='Unit', choices=WAVELENGTH_TYPE_CHOICES,
                                        widget=forms.Select(attrs={'data-wavelength-unit': ''}))
    wavelength_min = forms.FloatField(required=False, label='Min',
                                      widget=forms.NumberInput(attrs={'step': 'any', 'min': '0', 'placeholder': 'Min'}))
    wavelength_max = forms.FloatField(required=False, label='Max',
                                      widget=forms.NumberInput(attrs={'step': 'any', 'min': '0', 'placeholder': 'Max'}))
    observation_type = forms.ChoiceField(required=False, label='Observation type',
                                         choices=[('', 'Any'), ('Imaging', 'Imaging'),
                                                  ('Spectroscopy', 'Spectroscopy')])
    cone_radius = forms.FloatField(required=False, label='Cone Radius')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
                Column('wavelength_type', css_class='col-md-4'),
                Column('wavelength_min', css_class='col-md-4'),
                Column('wavelength_max', css_class='col-md-4'),
                css_class='row g-3'
            ),
            Row(
                Column('observation_type', css_class='col-md-4'),
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

    def clean(self):
        cleaned_data = super().clean()

        wavelength_type = cleaned_data.get("wavelength_type")
        wavelength_min = cleaned_data.get("wavelength_min")
        wavelength_max = cleaned_data.get("wavelength_max")

        if wavelength_type:
            if wavelength_min is None:
                cleaned_data["wavelength_min"] = 1
            if wavelength_max is None:
                cleaned_data["wavelength_max"] = 1000000

        return cleaned_data


class VisibilityPlotForm(forms.Form):
    observatories = forms.MultipleChoiceField(required=True, widget=forms.CheckboxSelectMultiple, label=False)
    begin = forms.DateTimeField(required=True, widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}))
    end = forms.DateTimeField(required=True, widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}))

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
                        'Update <span id="plot-spinner" class="htmx-indicator spinner-border spinner-border-sm ms-1" role="status"></span>'
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
