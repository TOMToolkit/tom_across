from django.apps import AppConfig
from django.urls import path, include


class TomAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tom_across'
    verbose_name = 'An ACROSS App for the TOM Toolkit'

    def target_detail_tabs(self):
        return [{'label': 'ACROSS', 'partial': 'tom_across/target_across.html',
                 'context': 'tom_across.templatetags.across_extras.version_context'}]

    def include_url_paths(self):
        urlpatterns = [
            path('across/', include(f'{self.name}.urls', namespace=f'{self.name}'))
        ]
        return urlpatterns
