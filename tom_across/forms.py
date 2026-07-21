from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, HTML, Field

import logging

logger = logging.getLogger(__name__)

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
            ),
            HTML(
                '<details class="mb-4 card card-body py-2 px-3">'
                '<summary class="cursor-pointer">Observatories</summary>'
                '<div class="mt-2">'
            ),
            Field('observatories', css_class='row row-cols-1 row-cols-md-3'),
            HTML('</div></details>'),
        )
