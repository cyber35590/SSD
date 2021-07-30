from django.apps import AppConfig
import sys

class BackendConfig(AppConfig):
    name = 'backend'

    def ready(self):
        BackendConfig.called+=1
        if ("migrate" in sys.argv) or ("makemigrations" in sys.argv): return
        from backend import server, scheduler
        server.init()
        scheduler.init()
