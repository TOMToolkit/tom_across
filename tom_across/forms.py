from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, HTML

import logging

logger = logging.getLogger(__name__)

class ObservationFilterForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    wavelength_type = forms.ChoiceField(
        required=False,
        choices=[('angstrom', 'angstrom'), ('nm', 'nm'), ('keV', 'keV')]
    )
    wavelength_min = forms.FloatField(required=False)
    wavelength_max = forms.FloatField(required=False)
    observation_type = forms.ChoiceField(
        required=False,
        choices=[('', 'Any'), ('imaging', 'Imaging'), ('spectroscopy', 'Spectroscopy')]
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
    begin = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}))
    end = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}))

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
            )
        )
