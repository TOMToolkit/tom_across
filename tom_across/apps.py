from django.apps import AppConfig
from django.urls import path, include


class TomAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tom_across'
    label = 'across'
    verbose_name = 'An ACROSS App for the TOM Toolkit'


    def target_detail_tabs(self):
        return [{"label": "ACROSS Tab", "partial": "tom_across/target_across.html"}]

    def include_url_paths(self):
        urlpatterns = [
            path(f'{self.label}/', include(f'{self.name}.urls', namespace=f'{self.label}'))
        ]
        return urlpatterns
