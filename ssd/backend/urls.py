from django.urls import path

from . import views

urlpatterns = [
    path('infos', views.node_infos),
    path('ping', views.node_ping),
    path('backup/request', views.node_backup_request),
    path('backup', views.node_backup),
    path('forward/request', views.node_forward_request),
    path('forward', views.node_forward),
    path('present', views.node_present,),
    path('query', views.node_query),
]