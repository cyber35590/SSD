from django.apps import AppConfig


class BackendConfig(AppConfig):
    name = 'backend'

    def ready(self):

        return super().ready()