from django.apps import AppConfig


class BackendConfig(AppConfig):
    name = 'backend'

    def ready(self):
        from backend import server, scheduler
        server.init()
        scheduler.init()
