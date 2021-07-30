from django.urls import path

from . import views
handler404 = 'backend.views.error_404'
urlpatterns = [
    path('infos', views.node_infos),
    path('ping', views.node_ping),
    path('backup/request', views.node_backup_request),
    path('backup', views.node_backup),
    path('forward/request', views.node_forward_request),
    path('forward', views.node_forward),
    path('list', views.node_list),
    path('register', views.node_discover,),
    path('query', views.node_query),
]