# tom_across

A TOM Toolkit app that integrates Astrophysics Cross-Observatory Science Support
([ACROSS](https://science.data.nasa.gov/data-sites/across)) functionality and features into the target page.

`tom_across` brings 2 main features to the target page as a separate tab. Each of these come with a form to
filter and query the ACROSS servers.

1. An observation table that displays observations within a cone search of the target's RA and Dec
2. A visibility plot for ACROSS observatories. 

## Installation

1. Install the package into your TOM environment:
    ```bash
    pip install tom-across
   ```

2. In your project `settings.py`, add `tom_across` to your `INSTALLED_APPS` setting:

```python
    INSTALLED_APPS = TOMTOOKIT_INSTALLED_APPS + [
    'custom_code',
    ...
    'tom_across',

    ]
```

3. Optionally add the following to your `settings.py` to alter the default initial query parameters on page load.
More parameters can be filtered upon through the front-end form.

```python
ACROSS_DEFAULT_ARGS = {
    'OBSERVATION_TABLE_DEFAULTS':{
        'cone_search_radius': 0.1,
    },
    'VISIBILITY_OBSERVATORY_DEFAULTS':[
        'JWST', 'HST', 'Swift'
    ]
}
```
