# tom_across app

A TOM Toolkit app that integrates ACROSS functionality and features into the target page.

## example settings.py variables for deployment

`ACROSS_OBSERVATION_DEFAULT_ARGS = 

URL for the across app to link the observations table and visibility tool.
`ACROSS_APP_URL = 'https://app.across.sciencecloud.nasa.gov'`

`ACROSS_VIS_OBSERVATORIES` is a list of observatory names to calculate visibility for from the target page on initial load.
More can be selected through the associated form.
`ACROSS_VIS_OBSERVATORIES = ['JWST', 'HST', 'Swift']`
