from django.apps import AppConfig


class TomAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tom_across' \
    ''
    def target_detail_tabs(self):
        return [{"label": "ACROSS", "partial": "tom_across/target_across.html"}]
    
    def nav_items(self):
        return [{'partial': 'tom_across/partials/navbar_item.html'}]
