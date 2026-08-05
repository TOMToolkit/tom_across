# tom_across app

A TOM Toolkit app that integrates Astrophysics Cross-Observatory Science Support (`ACROSS <https://science.data.nasa.gov/data-sites/across>_`)
functionality and features into the target page.

## example settings.py variables for deployment

Default arguments to be passed through to make the observation table on page load
`ACROSS_OBSERVATION_DEFAULT_ARGS = {'status': 'planned', 'cone_search_radius': 0.1}`

URL for the across app to link the observations table and visibility tool.
`ACROSS_APP_URL = 'https://app.across.sciencecloud.nasa.gov'`

`ACROSS_VIS_OBSERVATORIES` is a list of observatory names to calculate visibility for from the target page on initial load.
More can be selected through the associated form.
`ACROSS_VIS_OBSERVATORIES = ['JWST', 'HST', 'Swift']`
